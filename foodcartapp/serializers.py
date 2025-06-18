from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField 
from .models import Product, Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    phonenumber = PhoneNumberField()
    products = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
        extra_kwargs = {
            'firstname': {'source': 'first_name'},
            'lastname': {'source': 'last_name'},
            'phonenumber': {'source': 'phone_number'},
        }

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data['phone_number'],
            address=validated_data['address']
        )

        for product_data in products_data:
            OrderItem.objects.create(
                order=order,
                product=product_data['product'],
                quantity=product_data['quantity']
            )

        return order


class OrderResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address']
        extra_kwargs = {
            'firstname': {'source': 'first_name'},
            'lastname': {'source': 'last_name'},
            'phonenumber': {'source': 'phone_number'},
        }
