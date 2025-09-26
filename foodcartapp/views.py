import json
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response


from .models import Product
from .models import Order
from .models import OrderProduct


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    order_from_site = request.data
    print(order_from_site)
    firstname = order_from_site['firstname']
    lastname = order_from_site['lastname']
    phonenumber = order_from_site['phonenumber']
    address = order_from_site['address']

    order = Order.objects.create(
        firstname=firstname,
        lastname=lastname,
        phonenumber = phonenumber,
        address = address
    )

    ordered_products = order_from_site['products']
    for product in ordered_products:
        product_id = product['product']
        quantity = product['quantity']

        ordered_product = OrderProduct.objects.create(
            order_id = order.id,
            product_id = product_id,
            quantity = quantity
        )
    return Response({})


# @api_view(['GET'])
# def test_api(request):
#     orders = models.Order.objects.all()
#     processed_order = []
#     for order in orders:
#         processed_order.append({
#             'firstname':order.firstname,
#             'lastname:': order.lastname,
#             'phonenumber': order.phonenumber,
#             'address': order.address
#         })

#     return Response(processed_order)
    
    

