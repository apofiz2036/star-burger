from django.http import JsonResponse
from django.templatetags.static import static
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view
from rest_framework.response import Response

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


@api_view(['POST'])
def register_order(request):
    order_data = request.data

    #  Проверка поля products
    if 'products' not in order_data:
        return Response({'error': 'Нет обязательного поля products.'}, status=400)
    if not isinstance(order_data['products'], list):
        return Response({'error': 'Поле products должно быть списком'}, status=400)
    if len(order_data['products']) == 0:
        return Response({'error': 'Поле products не может быть пустым'}, status=400)

    # Проверка поля firstname
    if 'firstname' not in order_data:
        return Response({'error': 'Нет обязательного поля firstname.'}, status=400)
    if not isinstance(order_data['firstname'], str) or not order_data['firstname'].strip():
        return Response({'error': 'Поле firstname должно быть не пустой строкой'}, status=400)

    # Проверка поля lastname
    if 'lastname' in order_data and not isinstance(order_data['lastname'], str):
        return Response({'error': 'Поле lastname должно быть строкой'}, status=400)

    # Проверка поля phonenumber
    if 'phonenumber' not in order_data:
        return Response({'error': 'Нет обязательного поля phonenumber.'}, status=400)

    phone = order_data['phonenumber'].strip()

    if not phone:
        return Response({'error': 'Номер телефона не может быть пустым'}, status=400)
    if phone.startswith('8') and len(phone) == 11:
        phone = '+7' + phone[1:]
    elif phone.startswith('7') and len(phone) == 11:
        phone = '+' + phone

    try:
        phone_number = to_python(phone)
        if not phone_number or not phone_number.is_valid():
            return Response({'error': 'Введите номер в формате +7XXX... или 8XXX...'}, status=400)
    except Exception:
        return Response({'error': 'Неверный формат номера'}, status=400)

    order_data['phonenumber'] = str(phone_number)

    # Проверка поля address
    if 'address' not in order_data:
        return Response({'error': 'Нет обязательного поля address.'}, status=400)
    if not isinstance(order_data['address'], str) or not order_data['address'].strip():
        return Response({'error': 'Поле address должно быть не пустой строкой'}, status=400)

    # Создание заказа
    order = Order.objects.create(
        first_name=order_data['firstname'],
        last_name=order_data.get('lastname', ''),
        phone_number=order_data['phonenumber'],
        address=order_data['address']
    )

    # Проверка продуктов
    for product_item in order_data['products']:
        product_id = product_item['product']
        quantity = product_item['quantity']

        if not isinstance(quantity, int) or quantity <= 0:
            return Response({'error': 'Количество должно быть целым числом больше нуля'}, status=400)

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({'error': f'Продукт {product_id} не найден'}, status=400)

        OrderItem.objects.create(
            order=order,
            product=product,  #!!!!!!!!!!!!!!!!!!!!!!!!!! product_id=product_item['product']
            quantity=product_item['quantity']
        )

    return Response({'status': 'ok'})
