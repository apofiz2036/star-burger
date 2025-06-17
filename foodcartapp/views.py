from django.http import JsonResponse
from django.templatetags.static import static
from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product
from .models import Order
from .models import OrderItem

from .serializers import OrderItemSerializer, OrderSerializer, OrderResponseSerializer


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


def fetch_and_save_coordinates(instance):
    try:
        from geocoder import fetch_coordinates 
        lon, lat = fetch_coordinates(instance.address)
        instance.address_lon = lon
        instance.address_lat = lat
    except Exception as e:
        instance.address_lon = None
        instance.address_lat = None
    instance.save()


@api_view(['GET', 'POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        order = serializer.save()
        fetch_and_save_coordinates(order)
        response_serializer = OrderResponseSerializer(order)
        return Response(response_serializer.data)
