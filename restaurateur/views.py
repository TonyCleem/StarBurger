import os
import requests
from geopy import distance
from dotenv import load_dotenv

from django import forms
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test

from foodcartapp.models import Order, Product, Restaurant


class Login(forms.Form):
    username = forms.CharField(
        label="Логин",
        max_length=75,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Укажите имя пользователя"}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        max_length=75,
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите пароль"}
        ),
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={"form": form})

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(
            request,
            "login.html",
            context={
                "form": form,
                "ivalid": True,
            },
        )


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("restaurateur:login")


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_products(request):
    restaurants = list(Restaurant.objects.order_by("name"))
    products = list(Product.objects.prefetch_related("menu_items"))

    products_with_restaurant_availability = []
    for product in products:
        availability = {
            item.restaurant_id: item.availability for item in product.menu_items.all()
        }
        ordered_availability = [
            availability.get(restaurant.id, False) for restaurant in restaurants
        ]

        products_with_restaurant_availability.append((product, ordered_availability))

    return render(
        request,
        template_name="products_list.html",
        context={
            "products_with_restaurant_availability": products_with_restaurant_availability,
            "restaurants": restaurants,
        },
    )


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_restaurants(request):
    return render(
        request,
        template_name="restaurants_list.html",
        context={
            "restaurants": Restaurant.objects.all(),
        },
    )


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_orders(request):
    load_dotenv()
    api_key = os.getenv("YANDEX_API_KEY")

    orders = (
        Order.objects.all()
        .with_total_price()
        .prefetch_related("position__product__menu_items__restaurant")
    )

    orders_with_restaurants = []
    for order in orders:
        orders_with_restaurants.append(
            {
                "order": order,
                "restaurant_status": build_status(api_key, order),
            }
        )

    return render(
        request,
        "order_items.html",
        {"orders_with_restaurants": orders_with_restaurants},
    )


def get_order_restaurants(order):
    order_products = order.position.values_list("product_id", flat=True)

    return (
        Restaurant.objects.filter(
            menu_items__availability=True, menu_items__product_id__in=order_products
        )
        .annotate(matches=Count("menu_items"))
        .filter(matches=len(order_products))
    )


def calc_distances(api_key, order, restaurants):
    order_coords = fetch_coordinates(api_key, order.address)
    if not order_coords:
        raise ValueError

    result = []
    for restaurant in restaurants:
        coordinates = fetch_coordinates(api_key, restaurant.address)
        if not coordinates:
            raise ValueError

        dist = distance.distance(order_coords, coordinates).km
        result.append(
            {
                "name": restaurant.name,
                "distance": round(dist, 3),
            }
        )

    return sorted(result, key=lambda restaurant_info: restaurant_info["distance"])


def build_status(api_key, order):
    if order.confirmed_restaurant:
        return {
            "type": "confirmed",
            "name": order.confirmed_restaurant.name,
        }

    restaurants = get_order_restaurants(order)
    if not restaurants:
        return {
            "type": "error",
            "message": "Ошибка определения координат",
        }

    try:
        dist = calc_distances(api_key, order, restaurants)
        return {
            "type": "suggested",
            "restaurants": dist,
        }
    except Exception:
        return {
            "type": "error",
            "message": "Ошибка определения координат",
        }


from geolocation.models import PlaceCoordinates


def fetch_coordinates(apikey, address):
    try:
        cached = PlaceCoordinates.objects.get(address=address)
        return (cached.lat, cached.lon)
    except PlaceCoordinates.DoesNotExist:
        pass

    try:
        response = requests.get(
            "https://geocode-maps.yandex.ru/1.x",
            params={
                "geocode": address,
                "apikey": apikey,
                "format": "json",
            },
            timeout=3,
        )
        response.raise_for_status()
        found_places = response.json()["response"]["GeoObjectCollection"][
            "featureMember"
        ]
        if not found_places:
            return None

        lon, lat = found_places[0]["GeoObject"]["Point"]["pos"].split(" ")
        PlaceCoordinates.objects.create(address=address, lat=float(lat), lon=float(lon))
        return (float(lat), float(lon))
    except Exception:
        return None
