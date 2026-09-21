# store/tests.py
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import Store, Product, Order, OrderItem, Review


def register(client, username, account_type, password="TestPass123!"):
    """Helper: register a user of the given account_type and return the
    created User instance.
    """
    client.post(
        reverse("register"),
        {
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "password_confirm": password,
            "account_type": account_type,
        },
    )
    return User.objects.get(username=username)


class RegistrationTest(TestCase):
    def test_vendor_registration_adds_vendor_group(self):
        register(self.client, "vendoruser", "vendor")
        user = User.objects.get(username="vendoruser")
        self.assertTrue(user.groups.filter(name="Vendors").exists())

    def test_buyer_registration_adds_buyer_group(self):
        register(self.client, "buyeruser", "buyer")
        user = User.objects.get(username="buyeruser")
        self.assertTrue(user.groups.filter(name="Buyers").exists())

    def test_registration_rejects_duplicate_username(self):
        register(self.client, "dupeuser", "buyer")
        response = self.client.post(
            reverse("register"),
            {
                "username": "dupeuser",
                "email": "dupeuser2@example.com",
                "password": "TestPass123!",
                "password_confirm": "TestPass123!",
                "account_type": "buyer",
            },
        )
        self.assertEqual(User.objects.filter(username="dupeuser").count(), 1)
        self.assertContains(response, "already taken")

    def test_registration_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "mismatchuser",
                "email": "mismatch@example.com",
                "password": "TestPass123!",
                "password_confirm": "Different123!",
                "account_type": "buyer",
            },
        )
        self.assertFalse(User.objects.filter(username="mismatchuser").exists())
        self.assertContains(response, "do not match")


class StorePermissionTest(TestCase):
    def setUp(self):
        self.vendor = register(self.client, "vendorperm", "vendor")

    def test_vendor_can_view_store_create_form(self):
        response = self.client.get(reverse("store_create"))
        self.assertEqual(response.status_code, 200)

    def test_buyer_is_redirected_away_from_store_create_form(self):
        self.client.logout()
        register(self.client, "buyerperm", "buyer")
        response = self.client.get(reverse("store_create"))
        self.assertEqual(response.status_code, 302)
        self.assertNotContains(self.client.get(reverse("store_create"), follow=True), "New store")

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("store_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_vendor_can_create_store(self):
        response = self.client.post(
            reverse("store_create"), {"name": "Test Store", "description": "A store"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Store.objects.filter(name="Test Store", owner=self.vendor).exists())

    def test_non_owner_vendor_cannot_edit_another_vendors_store(self):
        store = Store.objects.create(owner=self.vendor, name="Owned Store")
        self.client.logout()
        register(self.client, "othervendor", "vendor")
        response = self.client.post(
            reverse("store_update", args=[store.pk]),
            {"name": "Hijacked name", "description": ""},
        )
        store.refresh_from_db()
        self.assertNotEqual(store.name, "Hijacked name")
        self.assertEqual(response.status_code, 302)


class ProductAndCartTest(TestCase):
    def setUp(self):
        self.vendor = register(self.client, "vendorcart", "vendor")
        self.store = Store.objects.create(owner=self.vendor, name="Cart Test Store")
        self.product = Product.objects.create(
            store=self.store, name="Widget", price="19.99", stock=5
        )
        self.client.logout()
        self.buyer = register(self.client, "buyercart", "buyer")

    def test_product_list_shows_product(self):
        response = self.client.get(reverse("product_list"))
        self.assertContains(response, "Widget")

    def test_add_to_cart_stores_item_in_session(self):
        self.client.post(reverse("add_to_cart", args=[self.product.pk]), {"quantity": 2})
        cart = self.client.session.get("cart", {})
        self.assertEqual(cart.get(str(self.product.pk)), 2)

    def test_view_cart_shows_line_total(self):
        self.client.post(reverse("add_to_cart", args=[self.product.pk]), {"quantity": 2})
        response = self.client.get(reverse("view_cart"))
        self.assertContains(response, "Widget")
        self.assertContains(response, "39.98")

    def test_checkout_creates_order_and_clears_cart(self):
        self.client.post(reverse("add_to_cart", args=[self.product.pk]), {"quantity": 2})
        response = self.client.post(reverse("checkout"))
        self.assertEqual(response.status_code, 302)

        order = Order.objects.get(buyer=self.buyer)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertEqual(str(order.total), "39.98")

        cart = self.client.session.get("cart", {})
        self.assertEqual(cart, {})

    def test_checkout_decrements_stock(self):
        self.client.post(reverse("add_to_cart", args=[self.product.pk]), {"quantity": 2})
        self.client.post(reverse("checkout"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_checkout_sends_invoice_email(self):
        self.client.post(reverse("add_to_cart", args=[self.product.pk]), {"quantity": 1})
        self.client.post(reverse("checkout"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("invoice", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, [self.buyer.email])

    def test_checkout_with_empty_cart_does_not_create_order(self):
        orders_before = Order.objects.count()
        self.client.post(reverse("checkout"))
        self.assertEqual(Order.objects.count(), orders_before)


class ReviewTest(TestCase):
    def setUp(self):
        self.vendor = register(self.client, "vendorreview", "vendor")
        self.store = Store.objects.create(owner=self.vendor, name="Review Test Store")
        self.product = Product.objects.create(
            store=self.store, name="Reviewed Thing", price="9.99", stock=10
        )
        self.client.logout()

    def test_review_is_verified_after_purchase(self):
        register(self.client, "verifiedbuyer", "buyer")
        self.client.post(reverse("add_to_cart", args=[self.product.pk]), {"quantity": 1})
        self.client.post(reverse("checkout"))

        self.client.post(
            reverse("leave_review", args=[self.product.pk]),
            {"rating": 5, "comment": "Loved it"},
        )
        review = Review.objects.get(product=self.product)
        self.assertTrue(review.verified)

    def test_review_is_unverified_without_purchase(self):
        register(self.client, "unverifiedbuyer", "buyer")
        self.client.post(
            reverse("leave_review", args=[self.product.pk]),
            {"rating": 3, "comment": "Looks okay"},
        )
        review = Review.objects.get(product=self.product)
        self.assertFalse(review.verified)


class PasswordResetTest(TestCase):
    def setUp(self):
        self.user = register(self.client, "forgetfuluser", "buyer")
        self.client.logout()

    def test_forgot_password_sends_email_for_known_address(self):
        self.client.post(reverse("forgot_password"), {"email": self.user.email})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset", mail.outbox[0].subject.lower())

    def test_forgot_password_does_not_error_for_unknown_address(self):
        response = self.client.post(
            reverse("forgot_password"), {"email": "nobody@example.com"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_password_with_invalid_token_redirects(self):
        response = self.client.get(reverse("reset_password", args=["not-a-real-token"]))
        self.assertEqual(response.status_code, 302)

    def test_full_reset_flow_changes_password(self):
        self.client.post(reverse("forgot_password"), {"email": self.user.email})
        email_body = mail.outbox[0].body
        # Extract the token from the reset URL in the email body.
        token = email_body.strip().split("/")[-2]

        response = self.client.get(reverse("reset_password", args=[token]))
        self.assertEqual(response.status_code, 200)

        self.client.post(
            reverse("reset_password", args=[token]),
            {"password": "NewPass456!", "password_confirm": "NewPass456!"},
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))

class BuyerOnlyCartTest(TestCase):
    """Vendors must not be able to use cart / checkout functionality."""

    def setUp(self):
        self.vendor = register(self.client, "vendorcart2", "vendor")
        self.store = Store.objects.create(owner=self.vendor, name="Cart Store")
        self.product = Product.objects.create(
            store=self.store, name="Widget", price="10.00", stock=5
        )

    def test_vendor_cannot_add_to_cart(self):
        self.client.post(
            reverse("add_to_cart", args=[self.product.pk]), {"quantity": 1}
        )
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_vendor_cannot_view_cart(self):
        response = self.client.get(reverse("view_cart"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("/cart/", response.url)

    def test_anonymous_cannot_add_to_cart(self):
        self.client.logout()
        response = self.client.post(
            reverse("add_to_cart", args=[self.product.pk]), {"quantity": 1}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)


class UniqueEmailTest(TestCase):
    def test_registration_rejects_duplicate_email(self):
        register(self.client, "firstbuyer", "buyer")
        response = self.client.post(
            reverse("register"),
            {
                "username": "secondbuyer",
                "email": "firstbuyer@example.com",   # same as first
                "password": "TestPass123!",
                "password_confirm": "TestPass123!",
                "account_type": "buyer",
            },
        )
        self.assertEqual(
            User.objects.filter(email="firstbuyer@example.com").count(), 1
        )
        self.assertContains(response, "already exists")

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        register(self.client, "casebuyer1", "buyer")
        response = self.client.post(
            reverse("register"),
            {
                "username": "casebuyer2",
                "email": "CaseBuyer1@Example.com",
                "password": "TestPass123!",
                "password_confirm": "TestPass123!",
                "account_type": "buyer",
            },
        )
        self.assertContains(response, "already exists")


class StockEnforcementTest(TestCase):
    def setUp(self):
        self.vendor = register(self.client, "vendorstock", "vendor")
        store = Store.objects.create(owner=self.vendor, name="Stock Store")
        self.product = Product.objects.create(
            store=store, name="Thing", price="5.00", stock=3
        )
        self.client.logout()
        register(self.client, "buyster", "buyer")

    def test_add_to_cart_over_stock_is_rejected(self):
        self.client.post(
            reverse("add_to_cart", args=[self.product.pk]), {"quantity": 4}
        )
        cart = self.client.session.get("cart", {})
        self.assertEqual(cart.get(str(self.product.pk), 0), 0)

    def test_add_to_cart_accumulates_and_checks_running_total(self):
        self.client.post(
            reverse("add_to_cart", args=[self.product.pk]), {"quantity": 2}
        )
        # Cart already has 2, stock is 3. Adding 2 more would push it to 4.
        self.client.post(
            reverse("add_to_cart", args=[self.product.pk]), {"quantity": 2}
        )
        cart = self.client.session.get("cart", {})
        self.assertEqual(cart.get(str(self.product.pk)), 2)

    def test_checkout_aborts_when_stock_dropped_behind_the_scenes(self):
        # Buyer adds 3; stock drops to 1 behind their back.
        self.client.post(
            reverse("add_to_cart", args=[self.product.pk]), {"quantity": 3}
        )
        self.product.stock = 1
        self.product.save()

        orders_before = Order.objects.count()
        response = self.client.post(reverse("checkout"), follow=True)
        self.assertEqual(Order.objects.count(), orders_before)
        self.assertContains(response, "only 1 in stock")

    def test_cart_page_flags_over_stock_items(self):
        self.client.post(
            reverse("add_to_cart", args=[self.product.pk]), {"quantity": 3}
        )
        self.product.stock = 1
        self.product.save()

        response = self.client.get(reverse("view_cart"))
        self.assertContains(response, "exceed available stock")


class InvoiceEmailTest(TestCase):
    def setUp(self):
        self.vendor = register(self.client, "vendorinvoice", "vendor")
        store = Store.objects.create(owner=self.vendor, name="Invoice Store")
        self.product = Product.objects.create(
            store=store, name="Invoice Thing", price="7.50", stock=10
        )
        self.client.logout()
        register(self.client, "buyerinvoice", "buyer")

    def test_invoice_email_contains_order_lines(self):
        self.client.post(
            reverse("add_to_cart", args=[self.product.pk]), {"quantity": 2}
        )
        self.client.post(reverse("checkout"))

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertIn("Invoice Thing", body)
        self.assertIn("2 x Invoice Thing", body)
        self.assertIn("15.00", body)   # 2 × 7.50