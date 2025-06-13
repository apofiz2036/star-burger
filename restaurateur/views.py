from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views


from foodcartapp.models import Product, Restaurant, Order

from geopy.distance import distance
import requests
from dotenv import load_dotenv
import os


def calculate_distance(restaurant_lat, restaurant_lon, order_lat, order_lon):
    if None in (restaurant_lat, restaurant_lon, order_lat, order_lon):
        None
    else:
        return distance((restaurant_lat, restaurant_lon), (order_lat, order_lon)).km


def fetch_coordinates(address):
    load_dotenv()
    base_url = "https://geocode-maps.yandex.ru/1.x"
    apikey = os.getenv('YANDEX_API')
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.with_total_cost().prefetch_related('order_items')
    active_orders = orders.exclude(order_status='COMPLETED')

    for order in active_orders:
        try:
            order_lon, order_lat = fetch_coordinates(order.address)
        except Exception as e:
            order_lon, order_lat = None, None

        available_restaurants = []
        for restaurant in order.get_available_restaurants():
            try:
                restaurant_lon, restaurant_lat = fetch_coordinates(restaurant.address)
                dist = calculate_distance(
                    restaurant_lon, restaurant_lat,
                    order_lon, order_lat
                ) if all((restaurant_lat, restaurant_lon, order_lat, order_lon)) else None
            except Exception as e:
                dist = None

            available_restaurants.append({
                'name': restaurant.name,
                'distance': dist
            })

        order.available_restaurants = sorted(
            available_restaurants,
            key=lambda x: x['distance'] if x['distance'] is not None else float('inf')
        )

    return render(
        request,
        template_name='order_items.html',
        context={'order_items': active_orders},
    )
