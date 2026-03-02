from geopy import distance
from operator import itemgetter

from django import forms
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from geolocation.models import PlaceCoordinates

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
                if user.is_staff:
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
    return user.is_staff


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
    orders = (
        Order.objects.all()
        .with_total_price()
        .with_available_restaurants()
        .prefetch_related("positions__product")
    )

    orders_with_restaurants = []
    for order in orders:
        orders_with_restaurants.append(
            {
                "order": order,
                "restaurant_status": build_status(order),
            }
        )

    return render(
        request,
        "order_items.html",
        {"orders_with_restaurants": orders_with_restaurants},
    )


def calc_distances(order, restaurants):
    all_addresses = [order.address]
    for restaurant in restaurants:
        all_addresses.append(restaurant.address)

    coordinates_query = PlaceCoordinates.objects.filter(address__in=all_addresses)
    coordinates_by_address = {}
    for coord in coordinates_query:
        coordinates_by_address[coord.address] = (coord.lat, coord.lon)

    order_coords = coordinates_by_address.get(order.address)
    if not order_coords:
        raise ValueError

    result = []
    for restaurant in restaurants:
        restaurant_coords = coordinates_by_address.get(restaurant.address)
        if not restaurant_coords:
            raise ValueError

        dist = distance.distance(order_coords, restaurant_coords).km
        result.append(
            {
                "name": restaurant.name,
                "distance": round(dist, 3),
            }
        )

    result.sort(key=itemgetter("distance"))
    return result


def build_status(order):
    if order.confirmed_restaurant:
        return {
            "type": "confirmed",
            "name": order.confirmed_restaurant.name,
        }

    restaurants = order.available_restaurants
    if not restaurants:
        return {
            "type": "error",
            "message": "Ошибка определения координат",
        }

    try:
        dist = calc_distances(order, restaurants)
        return {
            "type": "suggested",
            "restaurants": dist,
        }
    except Exception:
        return {
            "type": "error",
            "message": "Ошибка определения координат",
        }
