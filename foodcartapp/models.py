from collections import defaultdict

from django.db import models
from django.db.models import F, Sum
from django.core.validators import MinValueValidator
from django.utils import timezone

from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField("название", max_length=50)
    address = models.CharField(
        "адрес",
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        "контактный телефон",
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = "ресторан"
        verbose_name_plural = "рестораны"

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = RestaurantMenuItem.objects.filter(availability=True).values_list(
            "product"
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField("название", max_length=50)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("название", max_length=50)
    category = models.ForeignKey(
        ProductCategory,
        verbose_name="категория",
        related_name="products",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        "цена", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )
    image = models.ImageField("картинка")
    special_status = models.BooleanField(
        "спец.предложение",
        default=False,
        db_index=True,
    )
    description = models.TextField(
        "описание",
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name="menu_items",
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="menu_items",
        verbose_name="продукт",
    )
    availability = models.BooleanField("в продаже", default=True, db_index=True)

    class Meta:
        verbose_name = "пункт меню ресторана"
        verbose_name_plural = "пункты меню ресторана"
        unique_together = [["restaurant", "product"]]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def with_total_price(self):
        return self.annotate(
            total_price=Sum(F("position__product__price") * F("position__quantity"))
        )

    def with_available_restaurants(self):
        menu_items = RestaurantMenuItem.objects.filter(
            availability=True
        ).select_related('restaurant', 'product')

        restaurant_products = defaultdict(set)
        for item in menu_items:
            restaurant_products[item.restaurant].add(item.product_id)

        orders = list(self)

        for order in orders:
            order_products = set(order.positions.values_list('product_id', flat=True))

            available_restaurants = []

            for restaurant, products in restaurant_products.items():
                if order_products.issubset(products):
                    available_restaurants.append(restaurant)

            order.available_restaurants = available_restaurants

        return orders


class Order(models.Model):
    STATUS_CHOISE = {
        "manager": "В обработке",
        "restaurant": "Собираем заказ",
        "courier": "Заказ в пути",
        "client": "Доставлено",
    }

    PAYMENT_METHOD = {
        "cash": "Наличностью",
        "non-cash": "Электронно",
    }

    status = models.CharField(
        max_length=50, choices=STATUS_CHOISE, default="Не обработан", db_index=True
    )
    firstname = models.CharField("Имя", max_length=50)
    lastname = models.CharField("Фамилия", max_length=50)
    phonenumber = PhoneNumberField(
        "Номер телефона", help_text="Контактный телефон", db_index=True
    )
    address = models.TextField("Адрес")
    comment = models.TextField("Комментарий", null=True, blank=True)
    registration_date = models.DateTimeField(
        "Дата регистрации", default=timezone.now, db_index=True
    )
    call_date = models.DateTimeField(
        "Дата звонка", null=True, blank=True, db_index=True
    )
    delivery_date = models.DateTimeField(
        "Дата доставки", null=True, blank=True, db_index=True
    )
    payment_method = models.CharField(
        "Способ оплаты", choices=PAYMENT_METHOD, default="", blank=True, db_index=True
    )
    confirmed_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name="Подтверждённый ресторан",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="confirmed_orders",
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.address}"


class OrderProduct(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        related_name="positions",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        verbose_name="Продукт",
        related_name="ordered_products",
        on_delete=models.CASCADE,
    )
    product_price = models.DecimalField(
        "Цена",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    quantity = models.IntegerField(default=1, verbose_name="количество продуктов")

    class Meta:
        verbose_name_plural = "Детали заказа"

    def __str__(self):
        return f"{self.product.name}"
