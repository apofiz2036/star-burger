from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import F, Sum


class OrderQuerySet(models.QuerySet):
    def with_total_cost(self):
        return self.annotate(
            total_cost=Sum(F('order_items__quantity') * F('order_items__fixed_price'))
        )


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    STATUS = (
        ('MANAGER', 'Менеджер'),
        ('RESTAURANT', 'Ресторан'),
        ('COURIER', 'Курьер'),
        ('COMPLETED', 'Завершён')
    )

    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(
        max_length=100,
        verbose_name='Фамилия',
        null=True,
        blank=True
    )
    phone_number = PhoneNumberField(verbose_name='Телефон')
    address = models.CharField(max_length=200, verbose_name='Адрес')
    products = models.ManyToManyField(
        Product,
        through='OrderItem',
        verbose_name='Товары'
    )
    objects = OrderQuerySet.as_manager()
    order_status = models.CharField(
        max_length=50,
        choices=STATUS,
        default='MANAGER',
        verbose_name='Статус заказа',
        db_index=True
    )

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'Заказ: {self.id}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='order_items',
        verbose_name='Заказ',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name='order_products',
        verbose_name='Товар',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )
    fixed_price = models.DecimalField(
        'Фиксированная цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=False,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.pk and self.fixed_price is None:
            self.fixed_price = self.product.price
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'
