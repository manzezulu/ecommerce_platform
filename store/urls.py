# store/urls.py
from django.urls import path

from . import views
from . import api_views

urlpatterns = [

    path("api/stores/", api_views.store_list_create, name="api_store_list"),
    path("api/stores/<int:pk>/", api_views.store_detail, name="api_store_detail"),
    path("api/stores/<int:store_pk>/products/", api_views.store_products, name="api_store_products"),
    path("api/products/<int:pk>/", api_views.product_detail, name="api_product_detail"),
    path("api/products/<int:pk>/reviews", api_views.product_reviews, name="api_product_reviews"),
    path("api/stores.xml/", api_views.stores_xml, name="api_stores_xml"),

    path("reddit/", views.reddit_feed, name="reddit_feed"),
    
    # Auth
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/<str:token>/", views.reset_password, name="reset_password"),

    # Products (public browsing)
    path("", views.product_list, name="product_list"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("product/<int:pk>/review/", views.leave_review, name="leave_review"),

    # Stores
    path("stores/mine/", views.my_stores, name="my_stores"),
    path("stores/new/", views.store_create, name="store_create"),
    path("stores/<int:pk>/", views.store_detail, name="store_detail"),
    path("stores/<int:pk>/edit/", views.store_update, name="store_update"),
    path("stores/<int:pk>/delete/", views.store_delete, name="store_delete"),
    path("stores/<int:store_pk>/products/new/", views.product_create, name="product_create"),

    # Products (vendor management)
    path("product/<int:pk>/edit/", views.product_update, name="product_update"),
    path("product/<int:pk>/delete/", views.product_delete, name="product_delete"),

    # Cart & checkout
    path("cart/", views.view_cart, name="view_cart"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
]
