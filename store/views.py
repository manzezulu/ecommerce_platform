# store/views.py
"""
Views for the store app.

Organised by area:
- Helpers (groups, cart helpers, decorators)
- Authentication (register, login, logout)
- Stores (vendor-only management)
- Products (vendor management, buyer browsing)
- Cart & checkout (buyers only)
- Reviews
- Password reset
"""

import secrets
from datetime import datetime, timedelta
from functools import wraps
from hashlib import sha1

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group, Permission
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .models import Store, Product, Order, OrderItem, Review, PasswordResetToken
from .forms import (
    RegisterForm,
    LoginForm,
    StoreForm,
    ProductForm,
    ReviewForm,
    AddToCartForm,
    ForgotPasswordForm,
    SetNewPasswordForm,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_groups_exist():
    """Create the Vendors and Buyers groups the first time they are needed.

    Assigning the appropriate Django permissions to each group keeps
    permission checks centralised — the views just ask whether the
    current user has, e.g., `store.add_store`.
    """
    vendors, _ = Group.objects.get_or_create(name="Vendors")
    buyers, _ = Group.objects.get_or_create(name="Buyers")

    vendor_codenames = [
        "add_store", "change_store", "delete_store", "view_store",
        "add_products", "change_products", "delete_products", "view_products",
    ]
    vendors.permissions.set(Permission.objects.filter(codename__in=vendor_codenames))

    buyer_codenames = ["view_store", "view_products"]
    buyers.permissions.set(Permission.objects.filter(codename__in=buyer_codenames))

    return vendors, buyers


def _is_buyer(user):
    """Return True if `user` is in the Buyers group."""
    return user.groups.filter(name="Buyers").exists()


def _is_vendor(user):
    """Return True if `user` is in the Vendors group."""
    return user.groups.filter(name="Vendors").exists()


def buyer_required(view_func):
    """Ensure the current user is a logged-in buyer.

    Anonymous users are redirected to the login page. Logged-in
    non-buyers (i.e. vendors) get an error message and are redirected to
    the product list — they must never be able to add to or view a
    cart, or place an order.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not _is_buyer(request.user):
            messages.error(request, "Only buyers can use the cart or place orders.")
            return redirect("product_list")
        return view_func(request, *args, **kwargs)
    return _wrapped


def _get_cart(request):
    """Return the cart dict from the session (or an empty dict)."""
    return request.session.get("cart", {})


def _save_cart(request, cart):
    """Persist the cart dict back into the session."""
    request.session["cart"] = cart
    request.session.modified = True


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def register_user(request):
    """Register a new user as either a buyer or a vendor.

    On success the new user is added to the matching group, logged in,
    and redirected to the product list. Validation (unique username and
    email, matching passwords) is enforced by `RegisterForm`.
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            vendors, buyers = _ensure_groups_exist()

            data = form.cleaned_data
            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],   # already lower-cased by clean_email
                password=data["password"],
            )
            user.groups.add(vendors if data["account_type"] == "vendor" else buyers)
            user.save()

            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("product_list")
    else:
        form = RegisterForm()
    return render(request, "store/register.html", {"form": form})


def login_user(request):
    """Handle login for both buyers and vendors.

    On GET, renders the login form. On POST, authenticates the supplied
    credentials and redirects to the product list on success.
    """
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                return redirect("product_list")
            form.add_error(None, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, "store/login.html", {"form": form})


def logout_user(request):
    """Log the current user out and redirect to the login page."""
    logout(request)
    return redirect("login")


# ---------------------------------------------------------------------------
# Stores (vendor-only management)
# ---------------------------------------------------------------------------

@login_required
def my_stores(request):
    """List all stores owned by the currently-logged-in vendor."""
    stores = Store.objects.filter(owner=request.user)
    return render(request, "store/my_stores.html", {"stores": stores})


def store_detail(request, pk):
    """Show a single store and all its products.

    The `is_owner` flag tells the template whether to render edit /
    delete controls for the current user.
    """
    store = get_object_or_404(Store, pk=pk)
    products = store.products.all()
    is_owner = request.user.is_authenticated and store.owner_id == request.user.id
    return render(
        request,
        "store/store_detail.html",
        {"store": store, "products": products, "is_owner": is_owner},
    )


@login_required
def store_create(request):
    """Create a new store owned by the current vendor."""
    if not request.user.has_perm("store.add_store"):
        messages.error(request, "You do not have permission to create a store.")
        return redirect("product_list")

    if request.method == "POST":
        form = StoreForm(request.POST)
        if form.is_valid():
            new_store = form.save(commit=False)
            new_store.owner = request.user
            new_store.save()
            return redirect("store_detail", pk=new_store.pk)
    else:
        form = StoreForm()
    return render(request, "store/store_form.html", {"form": form})


@login_required
def store_update(request, pk):
    """Edit a store — only the owning vendor may do so."""
    store = get_object_or_404(Store, pk=pk)
    if store.owner_id != request.user.id or not request.user.has_perm("store.change_store"):
        messages.error(request, "You do not have permission to edit this store.")
        return redirect("store_detail", pk=pk)

    if request.method == "POST":
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            return redirect("store_detail", pk=store.pk)
    else:
        form = StoreForm(instance=store)
    return render(request, "store/store_form.html", {"form": form})


@login_required
def store_delete(request, pk):
    """Delete a store and (via cascade) all its products."""
    store = get_object_or_404(Store, pk=pk)
    if store.owner_id != request.user.id or not request.user.has_perm("store.delete_store"):
        messages.error(request, "You do not have permission to delete this store.")
        return redirect("store_detail", pk=pk)

    if request.method == "POST":
        store.delete()
        return redirect("my_stores")
    return render(request, "store/store_confirm_delete.html", {"store": store})


# ---------------------------------------------------------------------------
# Products (vendor management, buyer browsing)
# ---------------------------------------------------------------------------

def product_list(request):
    """Public product list — anyone (including anonymous users) can browse."""
    products = Product.objects.select_related("store").all()
    return render(request, "store/product_list.html", {"products": products})


def product_detail(request, pk):
    """Show one product with its reviews and the add-to-cart form."""
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all()
    add_to_cart_form = AddToCartForm()
    review_form = ReviewForm()
    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "add_to_cart_form": add_to_cart_form,
            "review_form": review_form,
        },
    )


@login_required
def product_create(request, store_pk):
    """Add a product to a store — only the owning vendor may do so."""
    store = get_object_or_404(Store, pk=store_pk)
    has_permission = (
        request.user.has_perm("store.add_products")
        or request.user.has_perm("store.add_product")
    )
    if store.owner_id != request.user.id or not has_permission:
        messages.error(request, "You do not have permission to add products to this store.")
        return redirect("store_detail", pk=store_pk)

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()
            return redirect("store_detail", pk=store.pk)
    else:
        form = ProductForm()
    return render(request, "store/product_form.html", {"form": form, "store": store})


@login_required
def product_update(request, pk):
    """Edit a product — only the owning vendor may do so."""
    product = get_object_or_404(Product, pk=pk)
    has_permission = (
        request.user.has_perm("store.change_products")
        or request.user.has_perm("store.change_product")
    )
    if product.store.owner_id != request.user.id or not has_permission:
        messages.error(request, "You do not have permission to edit this product.")
        return redirect("product_detail", pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect("product_detail", pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, "store/product_form.html", {"form": form, "store": product.store})


@login_required
def product_delete(request, pk):
    """Delete a product — only the owning vendor may do so."""
    product = get_object_or_404(Product, pk=pk)
    has_permission = (
        request.user.has_perm("store.delete_products")
        or request.user.has_perm("store.delete_product")
    )
    if product.store.owner_id != request.user.id or not has_permission:
        messages.error(request, "You do not have permission to delete this product.")
        return redirect("product_detail", pk=pk)

    store_pk = product.store.pk
    if request.method == "POST":
        product.delete()
        return redirect("store_detail", pk=store_pk)
    return render(request, "store/product_confirm_delete.html", {"product": product})


# ---------------------------------------------------------------------------
# Cart & checkout (buyers only)
# ---------------------------------------------------------------------------

@buyer_required
def add_to_cart(request, pk):
    """Add `quantity` of the given product to the session cart.

    Rejects any addition that would push the combined quantity above
    the product's current stock, showing the buyer a clear error naming
    the product and the remaining quantity.
    """
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data["quantity"]
            cart = _get_cart(request)
            key = str(pk)
            new_quantity = cart.get(key, 0) + quantity

            if new_quantity > product.stock:
                messages.error(
                    request,
                    f"Only {product.stock} × {product.name} in stock "
                    f"(you already have {cart.get(key, 0)} in your cart).",
                )
                return redirect("product_detail", pk=pk)

            cart[key] = new_quantity
            _save_cart(request, cart)
            messages.success(request, f"Added {quantity} × {product.name} to your cart.")
    return redirect("product_detail", pk=pk)


@buyer_required
def view_cart(request):
    """Render the current session cart with line totals and a grand total.

    Each line is flagged if its quantity currently exceeds stock, so
    the template can warn the buyer and disable checkout before they
    try to place the order.
    """
    cart = _get_cart(request)
    items = []
    total = 0
    has_issue = False
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            continue
        line_total = product.price * quantity
        total += line_total
        over_stock = quantity > product.stock
        if over_stock:
            has_issue = True
        items.append({
            "product": product,
            "quantity": quantity,
            "line_total": line_total,
            "over_stock": over_stock,
        })
    return render(
        request,
        "store/cart.html",
        {"items": items, "total": total, "has_issue": has_issue},
    )


@buyer_required
def remove_from_cart(request, pk):
    """Remove the given product from the session cart."""
    cart = _get_cart(request)
    cart.pop(str(pk), None)
    _save_cart(request, cart)
    return redirect("view_cart")


@buyer_required
def checkout(request):
    """Turn the session cart into an Order.

    Re-validates every line against current stock *before* creating any
    database rows. If any line exceeds stock, no order is created and
    the buyer sees exactly which product is short so they can adjust
    their cart themselves.
    """
    cart = _get_cart(request)
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("view_cart")

    # --- Step 1: validate stock before touching the DB. --------------
    shortages = []
    resolved = []  # list of (product, quantity) ready for order creation
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            continue
        if quantity > product.stock:
            shortages.append((product, quantity, product.stock))
        else:
            resolved.append((product, quantity))

    if shortages:
        for product, wanted, available in shortages:
            messages.error(
                request,
                f"{product.name}: you asked for {wanted}, only {available} in stock. "
                f"Please update your cart.",
            )
        return redirect("view_cart")

    # --- Step 2: create the order. -----------------------------------
    order = Order.objects.create(buyer=request.user, total=0)
    total = 0
    for product, quantity in resolved:
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=quantity,
            price_at_purchase=product.price,
        )
        product.stock -= quantity
        product.save(update_fields=["stock"])
        total += product.price * quantity

    order.total = total
    order.save(update_fields=["total"])

    # Clear the cart now that it has been turned into an order.
    _save_cart(request, {})

    # Send the invoice and confirm to the buyer.
    if request.user.email:
        _send_invoice_email(request.user, order)
        messages.success(
            request,
            "Thank you! Your order has been placed. "
            "A copy of the invoice has been emailed to you.",
        )
    else:
        messages.success(request, "Thank you! Your order has been placed.")

    return redirect("order_detail", pk=order.pk)


def _send_invoice_email(user, order):
    """Build and send the plain-text invoice for `order` to `user`.

    Uses `settings.DEFAULT_FROM_EMAIL` and does not suppress errors, so
    a misconfigured backend surfaces as an exception during development
    rather than silently producing no email.
    """
    lines = [f"Thank you for your order, {user.username}!", "", "Order summary:"]
    for item in order.items.all():
        lines.append(
            f"  {item.quantity} x {item.product_name} "
            f"@ {item.price_at_purchase} = {item.line_total()}"
        )
    lines.append("")
    lines.append(f"Total: {order.total}")

    EmailMessage(
        subject=f"Your order #{order.pk} invoice",
        body="\n".join(lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    ).send()


@login_required
def order_detail(request, pk):
    """Show one order to its owner; anyone else is redirected away."""
    order = get_object_or_404(Order, pk=pk)
    if order.buyer_id != request.user.id:
        messages.error(request, "You do not have permission to view this order.")
        return redirect("product_list")
    return render(request, "store/order_detail.html", {"order": order})


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@login_required
def leave_review(request, pk):
    """Create a Review for the given product on behalf of the current user.

    The review is marked 'verified' if the reviewer has an order
    containing this product.
    """
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            has_purchased = OrderItem.objects.filter(
                order__buyer=request.user, product=product
            ).exists()

            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.verified = has_purchased
            review.save()
            messages.success(request, "Thanks for your review!")
    return redirect("product_detail", pk=pk)


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------

def forgot_password(request):
    """Accept an email and, if it matches a user, send a reset link.

    Always shows the same success message — the endpoint must not be
    usable to enumerate registered email addresses.
    """
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            # Use filter().first() so duplicate rows can never raise
            # MultipleObjectsReturned. (Duplicate emails are also
            # rejected at registration, but this stays defensive.)
            user = User.objects.filter(email__iexact=email).first()
            if user is not None:
                url = _generate_reset_url(request, user)
                _send_reset_email(user, url)

            messages.success(
                request,
                "If that email address is registered, a reset link has been sent.",
            )
            return redirect("login")
    else:
        form = ForgotPasswordForm()
    return render(request, "store/forgot_password.html", {"form": form})


def _generate_reset_url(request, user):
    """Create a PasswordResetToken and return the absolute reset URL.

    Only the SHA-1 hash of the token is stored in the database; the raw
    value lives solely in the email sent to the user.
    """
    token = secrets.token_urlsafe(16)
    PasswordResetToken.objects.create(
        user=user,
        token=sha1(token.encode()).hexdigest(),
        expiry_date=timezone.now() + timedelta(minutes=15),
    )
    path = reverse("reset_password", args=[token])
    return request.build_absolute_uri(path)


def _send_reset_email(user, url):
    """Send the password-reset email containing the reset link."""
    body = (
        f"Hi {user.username},\n\n"
        f"Use the link below to reset your password. It expires in 15 minutes.\n\n"
        f"{url}\n"
    )
    EmailMessage(
        subject="Password reset",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    ).send()


def reset_password(request, token):
    """Validate a reset token and, on POST, set the user's new password.

    Tokens are single-use (deleted on success), expire after 15 minutes,
    and are stored hashed.
    """
    hashed = sha1(token.encode()).hexdigest()
    reset_token = PasswordResetToken.objects.filter(
        token=hashed, used=False
    ).first()

    if reset_token is None:
        messages.error(request, "This reset link is invalid or has already been used.")
        return redirect("forgot_password")

    if reset_token.expiry_date < timezone.now():
        reset_token.delete()
        messages.error(request, "This reset link has expired. Please request a new one.")
        return redirect("forgot_password")

    if request.method == "POST":
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user = reset_token.user
            user.set_password(form.cleaned_data["password"])
            user.save()
            reset_token.delete()   # single-use; delete rather than flag
            messages.success(request, "Your password has been reset. You can now log in.")
            return redirect("login")
    else:
        form = SetNewPasswordForm()
    return render(request, "store/reset_password.html", {"form": form})