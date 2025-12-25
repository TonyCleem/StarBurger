from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, ValidationError

from .models import Order, OrderProduct, Product


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse(
        [
            {
                "title": "Burger",
                "src": static("burger.jpg"),
                "text": "Tasty Burger at your door step",
            },
            {
                "title": "Spices",
                "src": static("food.jpg"),
                "text": "All Cuisines",
            },
            {
                "title": "New York",
                "src": static("tasty.jpg"),
                "text": "Food is incomplete without a tasty dessert",
            },
        ],
        safe=False,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 4,
        },
    )


def product_list_api(request):
    products = Product.objects.select_related("category").available()

    dumped_products = []
    for product in products:
        dumped_product = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "special_status": product.special_status,
            "description": product.description,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
            }
            if product.category
            else None,
            "image": product.image.url,
            "restaurant": {
                "id": product.id,
                "name": product.name,
            },
        }
        dumped_products.append(dumped_product)
    return JsonResponse(
        dumped_products,
        safe=False,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 4,
        },
    )


class OrderProductSerlializer(ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ["product", "quantity"]


class OrderSerializer(ModelSerializer):
    products = OrderProductSerlializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ["firstname", "lastname", "phonenumber", "address", "products"]

    def validate_phonenumber(self, phonenumber):
        if not phonenumber:
            raise ValidationError("Это поле не может быть пустым.")
        if not phonenumber.startswith("+79") or len(phonenumber) != 12:
            raise ValidationError("Введен некорректный номер телефона.")
        return phonenumber


@transaction.atomic
@api_view(["POST"])
def register_order(request):
    order_serializer = OrderSerializer(data=request.data)
    order_serializer.is_valid(raise_exception=True)
    validated_data = order_serializer.validated_data

    order = Order.objects.create(
        firstname=validated_data["firstname"],
        lastname=validated_data["lastname"],
        address=validated_data["address"],
        phonenumber=validated_data["phonenumber"],
    )
    response_serializer = OrderSerializer(order)

    for product_position in validated_data["products"]:
        OrderProduct.objects.create(
            order=order,
            product=product_position["product"],
            quantity=product_position["quantity"],
            product_price=product_position["product"].price,
        )

    return Response(response_serializer.data, status=200)
