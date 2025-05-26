from django.http import JsonResponse
from django.templatetags.static import static
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import Serializer, IntegerField, CharField, ListField

from phonenumber_field.phonenumber import to_python

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


class OrderItemSerializer(Serializer):
    product = IntegerField()
    quantity = IntegerField(min_value=1)

    def validate_product(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError(f'Продукт {value} не найден')
        return value


class OrderSerializer(Serializer):
    firstname = CharField(max_length=50, required=True)
    lastname = CharField(max_length=50, required=False, allow_blank=True)
    phonenumber = CharField(max_length=20, required=True)
    address = CharField(max_length=100, required=True)
    products = ListField(
        child=OrderItemSerializer(),
        allow_empty=False
    )

    def validate_phonenumber(self, value):
        phone = value.strip()
        if phone.startswith('8') and len(phone) == 11:
            phone = '+7' + phone[1:]
        elif phone.startswith('7') and len(phone) == 12:
            phone = '+' + phone

        phone_number = to_python(phone)
        if not phone_number or not phone_number.is_valid():
            raise serializers.ValidationError('Введите номер в формате +7XXX... или 8XXX...')
        return str(phone_number)

@api_view(['GET', 'POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    order = Order.objects.create(
        first_name=serializer.validated_data['firstname'],
        last_name=serializer.validated_data.get('lastname', ''),
        phone_number=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address']
    )

    for product_item in serializer.validated_data['products']:
        OrderItem.objects.create(
            order=order,
            product_id=product_item['product'],
            quantity=product_item['quantity']
        )

    return Response({'status': 'ok'})
