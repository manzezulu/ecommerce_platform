# store/admin.py
from django.contrib import admin

from .models import Store, Product, Order, OrderItem, Review, PasswordResetToken


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    inlines = [ProductInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "price", "stock")
    list_filter = ("store",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "total", "created_at")
    inlines = [OrderItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "verified", "created_at")
    list_filter = ("verified", "rating")


admin.site.register(PasswordResetToken)
