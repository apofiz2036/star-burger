from django.http import JsonResponse
from django.templatetags.static import static

from rest_framework.decorators import api_view
from rest_framework.response import Response


from .models import Product
from .models import Order
from .models import OrderItem


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
    order_data = request.data

    if 'products' not in order_data:
        return Response({'error': 'Нет обязательного поле products.'}, status=400)
    if not isinstance(order_data['products'], list):
        return Response({'error': 'Поле products должно быть списком'}, status=400)
    if len(order_data['products']) == 0:
        return Response({'error': 'Поле products не может быть пустым'}, status=400)

    order = Order.objects.create(
        first_name=order_data['firstname'],
        last_name=order_data.get('lastname', ''),
        phone_number=order_data['phonenumber'],
        address=order_data['address']
    )
    for product_item in order_data['products']:
        OrderItem.objects.create(
            order=order,
            product_id=product_item['product'],
            quantity=product_item['quantity']
        )
    return Response({'status': 'ok'})
