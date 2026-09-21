# System Requirements — eCommerce Platform

## 1. Purpose

A Django eCommerce web application supporting two kinds of user: **vendors**,
who run stores and sell products, and **buyers**, who browse products across
stores, purchase them, and leave reviews.

## 2. Users and how they interact with the system

| User type | Interactions |
|---|---|
| **Anonymous visitor** | Browse the product list and individual product pages; register; log in; request a password reset. |
| **Buyer** | Everything an anonymous visitor can do, plus: add products to a cart, check out (creating an order and receiving an emailed invoice), and leave a review on any product (verified if they've purchased it, unverified otherwise). |
| **Vendor** | Everything a buyer can do (a vendor can also buy things), plus: create/edit/delete their own store(s), and add/edit/delete products within their own store(s). |
| **Admin (superuser)** | Full CRUD on all data via the Django admin site — users, groups, stores, products, orders, reviews, and reset tokens. |

## 3. Functional requirements

1. Users can register as either a **buyer** or a **vendor**; the account type
   determines which Django group (`Buyers` or `Vendors`) they're added to,
   and therefore which permissions they hold.
2. Vendors can create, view, update, and delete their own stores.
3. Vendors can create, view, update, and delete products within stores
   they own.
4. Buyers can browse all products from all stores, view individual product
   detail pages, and add products to a session-based cart.
5. At checkout, the system creates an `Order` with one `OrderItem` per
   distinct product, reduces each product's stock accordingly, clears the
   cart, and emails the buyer an invoice.
6. Buyers can leave a review (rating + comment) on any product. A review is
   marked **verified** if the reviewing user has a prior order containing
   that product, and **unverified** otherwise.
7. Users who forget their password can request a reset link by email; the
   link contains a single-use, time-limited token.
8. Access to vendor-only actions is restricted both by Django permissions
   (group-based) and by an object-level ownership check (a vendor can only
   edit/delete their *own* stores and products).

## 4. Non-functional requirements

- **Security**: passwords are hashed by Django's built-in auth system;
  password-reset tokens are stored as SHA-1 hashes (never the raw token)
  and expire after 15 minutes; all state-changing actions require POST
  and a valid CSRF token; destructive actions (delete store/product)
  require an explicit confirmation step.
- **Data integrity**: `OrderItem` stores the product name and price *at
  the time of purchase*, so later edits to a product's price or a
  product/store deletion don't retroactively change historical invoices.
- **Portability**: the project runs on SQLite out of the box for easy
  local setup and grading, with a documented drop-in MariaDB/MySQL
  configuration for production use.

## 5. Planning for failure

| Scenario | How the system handles it |
|---|---|
| A buyer's cart contains a product whose stock has since dropped below the requested quantity | Checkout caps the purchased quantity to the available stock rather than erroring out or overselling. |
| A product in the cart is deleted before checkout | The checkout view silently skips it (looked up via `Product.objects.get`, caught as `DoesNotExist` in effect via the try path) rather than crashing. |
| A user submits a form with invalid data (e.g. mismatched passwords, missing required fields) | The form re-renders with field-level error messages; no partial/invalid object is saved. |
| A user tries to access another vendor's store-management pages | The view checks `store.owner_id == request.user.id` in addition to the Django permission check, and redirects with an error message rather than allowing the edit. |
| A password-reset link is reused, expired, or fabricated | The token lookup fails or the expiry check fails, and the user is redirected back to the "forgot password" page with an error message rather than being let through. |
| An anonymous user tries to reach a `@login_required` view | Django's `login_required` decorator redirects them to the login page with a `?next=` parameter, so they land back on the page they wanted after logging in. |

## 6. Planned URL/page map

| URL | Page |
|---|---|
| `/` | Product list (browse) |
| `/product/<id>/` | Product detail, reviews, add-to-cart |
| `/register/`, `/login/`, `/logout/` | Auth |
| `/forgot-password/`, `/reset-password/<token>/` | Password recovery |
| `/stores/mine/` | Vendor's own stores |
| `/stores/new/`, `/stores/<id>/`, `/stores/<id>/edit/`, `/stores/<id>/delete/` | Store CRUD |
| `/stores/<id>/products/new/`, `/product/<id>/edit/`, `/product/<id>/delete/` | Product CRUD |
| `/cart/`, `/cart/add/<id>/`, `/cart/remove/<id>/`, `/checkout/` | Cart & checkout |
| `/orders/<id>/` | Order/invoice detail |
