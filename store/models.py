# store/models.py
from django.conf import settings
from django.db import models


class Store(models.Model):
    """A shop owned by a vendor, containing that vendor's products.

    Fields:
    - owner: ForeignKey to the vendor (User) who created the store.
    - name: CharField for the store's display name.
    - description: optional TextField describing the store.
    - created_at: DateTimeField set when the store is created.

    Methods:
    - __str__: Returns the store's name.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stores"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """A product listed for sale within a vendor's store.

    Fields:
    - store: ForeignKey to the Store this product belongs to.
    - name: CharField for the product name.
    - description: optional TextField.
    - price: DecimalField for the product's price.
    - stock: PositiveIntegerField for quantity available.
    - created_at: DateTimeField set when the product is created.

    Meta:
    - Declares custom permissions (add/change/delete/view_products) on
      top of Django's default per-model permissions, so views can check
      either the default or the custom codename.
    """

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        permissions = [
            ("add_products", "Can add products"),
            ("change_products", "Can change products"),
            ("delete_products", "Can delete products"),
            ("view_products", "Can view products"),
        ]

    def __str__(self):
        return self.name


class Order(models.Model):
    """An order placed by a buyer at checkout — one per checkout event,
    which may contain items from multiple stores.

    Fields:
    - buyer: ForeignKey to the User who placed the order.
    - created_at: DateTimeField set when the order is placed.
    - total: DecimalField storing the order's total price at checkout.
    """

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.buyer.username})"


class OrderItem(models.Model):
    """A single product line within an Order, capturing the quantity and
    price at the time of purchase (so later price changes on the
    Product don't retroactively change historical orders).
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    def line_total(self):
        return self.quantity * self.price_at_purchase


class Review(models.Model):
    """A buyer's review of a product.

    Fields:
    - product: ForeignKey to the reviewed Product.
    - user: ForeignKey to the reviewing User.
    - rating: PositiveSmallIntegerField from 1-5.
    - comment: TextField for the review text.
    - verified: BooleanField — True if the reviewing user has an Order
      containing this product (a verified purchase), False otherwise.
    - created_at: DateTimeField set when the review is created.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review of {self.product.name} by {self.user.username}"


class PasswordResetToken(models.Model):
    """A single-use, time-limited token allowing a user to reset their
    password after requesting a "forgot password" email.

    Fields:
    - user: ForeignKey to the User the token belongs to.
    - token: CharField storing a hash of the token (never the raw token).
    - expiry_date: DateTimeField after which the token is no longer valid.
    - used: BooleanField — True once the token has been consumed.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=500)
    expiry_date = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset token for {self.user.username}"
