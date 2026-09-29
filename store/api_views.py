# store/api_views.py
"""
RESTful API views for the store app.

Endpoints:
- GET  /api/stores/                 - list all stores (public)
- POST /api/stores/                 - create a store (auth: vendor)
- GET  /api/stores/<pk>/            - retrieve one store (public)
- GET  /api/stores/<pk>/products/   - list products in a store (public)
- POST /api/stores/<pk>/products/   - add a product (auth: store owner)
- GET  /api/products/<pk>/          - retrieve one product (public)
- GET  /api/products/<pk>/reviews/  - list reviews for a product (public)
"""

from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_xml.renderers import XMLRenderer

from .models import Store, Product
from .serializers import StoreSerializer, ProductSerializer, ReviewSerializer


# ---------------------------------------------------------------------------
# Stores
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@authentication_classes([BasicAuthentication, SessionAuthentication])
def store_list_create(request):
    """GET: list all stores. POST: create a new store for the logged-in vendor."""
    if request.method == "GET":
        stores = Store.objects.select_related("owner").prefetch_related("products").all()
        serializer = StoreSerializer(stores, many=True)
        return Response(serializer.data)

    # --- POST ---
    if not request.user.is_authenticated:
        return Response(
            {"error": "Authentication required to create a store."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if not request.user.has_perm("store.add_store"):
        return Response(
            {"error": "You do not have permission to create stores."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = StoreSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user)     # bind owner server-side
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def store_detail(request, pk):
    """Retrieve a single store (public)."""
    try:
        store = Store.objects.prefetch_related("products").get(pk=pk)
    except Store.DoesNotExist:
        return Response(
            {"error": "Store not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(StoreSerializer(store).data)


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@authentication_classes([BasicAuthentication, SessionAuthentication])
def store_products(request, store_pk):
    """GET: list products in a store. POST: add a product (owner only)."""
    try:
        store = Store.objects.get(pk=store_pk)
    except Store.DoesNotExist:
        return Response(
            {"error": "Store not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        products = store.products.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    # --- POST ---
    if not request.user.is_authenticated:
        return Response(
            {"error": "Authentication required to add products."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    # Only the store owner can add products to it.
    if store.owner_id != request.user.id:
        return Response(
            {"error": "You can only add products to your own store."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(store=store)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def product_detail(request, pk):
    """Retrieve a single product with its reviews (public)."""
    try:
        product = Product.objects.select_related("store").get(pk=pk)
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(ProductSerializer(product).data)


@api_view(["GET"])
def product_reviews(request, pk):
    """Retrieve all reviews for a product (public)."""
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    reviews = product.reviews.all()
    return Response(ReviewSerializer(reviews, many=True).data)


# ---------------------------------------------------------------------------
# XML demonstration endpoint (shows XML rendering on demand)
# ---------------------------------------------------------------------------

@api_view(["GET"])
@renderer_classes([XMLRenderer])
def stores_xml(request):
    """Force XML output for the store list — useful for the sequence diagram.

    Clients calling /api/stores.xml/ will always get XML back regardless
    of the Accept header.
    """
    stores = Store.objects.prefetch_related("products").all()
    return Response(StoreSerializer(stores, many=True).data)