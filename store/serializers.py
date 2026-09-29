# store/serializers.py
"""
DRF serializers for the store app.

These translate the Store, Product, and Review models into JSON/XML
so external clients can consume them via the API.
"""

from rest_framework import serializers

from .models import Store, Product, Review


class ReviewSerializer(serializers.ModelSerializer):
    """Serialize a single Review (read-only from the API's perspective)."""

    user = serializers.StringRelatedField(read_only=True)   # shows username
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id", "product", "product_name",
            "user", "rating", "comment",
            "verified", "created_at",
        ]
        read_only_fields = ["id", "user", "verified", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    """Serialize a Product, optionally including its reviews."""

    reviews = ReviewSerializer(many=True, read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "store", "store_name", "name", "description",
            "price", "stock", "created_at", "reviews",
        ]
        read_only_fields = ["id", "created_at"]


class StoreSerializer(serializers.ModelSerializer):
    """Serialize a Store, including its products and a vendor username.

    The `owner` field is read-only so clients can't spoof ownership;
    the view sets it from `request.user` on creation.
    """

    products = ProductSerializer(many=True, read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Store
        fields = [
            "id", "owner", "owner_username", "name",
            "description", "created_at", "products",
        ]
        read_only_fields = ["id", "owner", "created_at"]