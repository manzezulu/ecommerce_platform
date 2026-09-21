# Access Control & Data Security — eCommerce Platform

## Layers of access control

Access to vendor-only actions is enforced through **three independent
layers**, so that a gap in one layer doesn't expose the whole system:

1. **Authentication** (`@login_required`) — every view that changes data
   (creating/editing/deleting a store or product, adding to cart,
   checking out, leaving a review) requires a logged-in session. An
   anonymous visitor is redirected to `/login/?next=<page>` and lands back
   on the page they wanted after logging in.

2. **Group-based permissions** (`request.user.has_perm(...)`) —
   registering as a vendor adds the user to a `Vendors` Django group,
   which holds the `add_store`, `change_store`, `delete_store`, and
   `view_store` default permissions plus the custom `add_products`,
   `change_products`, `delete_products`, and `view_products` permissions
   declared on the `Product` model. Registering as a buyer adds the user
   to a `Buyers` group with read-only (`view_*`) permissions only. Views
   check the relevant permission before allowing an action, independent
   of who owns what.

3. **Object-level ownership checks** — Django's permission system is
   model-level, not row-level: by default *any* user with
   `change_store` could edit *any* store. Since two different vendors
   must not be able to edit each other's stores, every store/product
   management view additionally checks `store.owner_id ==
   request.user.id` (or the equivalent via `product.store.owner_id`)
   before allowing the action, redirecting with an error message
   otherwise.

## What this looks like per action

| Action | Login required? | Permission checked | Ownership checked? |
|---|---|---|---|
| Browse products / view a product | No | — | — |
| Add to cart / view cart / checkout | Yes | — | — (cart is per-session, per-user) |
| Leave a review | Yes | — | — (any logged-in user may review any product) |
| Create a store | Yes | `store.add_store` | N/A (no owner yet) |
| Edit / delete a store | Yes | `store.change_store` / `store.delete_store` | Yes — must be the store's owner |
| Add a product to a store | Yes | `store.add_products` | Yes — must own the store |
| Edit / delete a product | Yes | `store.change_products` / `store.delete_products` | Yes — must own the product's store |

## Data security

- **Passwords** are never stored in plain text — Django's `User` model
  hashes them automatically (`create_user()` / `set_password()`).
- **Password-reset tokens** are generated with Python's `secrets` module
  (cryptographically secure), and only a **SHA-1 hash** of the token is
  stored in the database — the raw token exists only in the emailed
  link, mirroring how the token model works in the reference
  authentication guide for this task. Tokens expire after 15 minutes and
  are deleted once expired or used, so a leaked/old link stops working.
- **CSRF protection** is on by default for every POST form via Django's
  `CsrfViewMiddleware` and `{% csrf_token %}` in every template.
- **Historical order data** (`OrderItem.product_name`,
  `price_at_purchase`) is snapshotted at checkout rather than always
  referencing the live `Product`, so a later price change or product
  deletion can't silently alter a past invoice.
- **Email enumeration** is avoided on the "forgot password" page — the
  same success message is shown whether or not the submitted email
  exists in the system, so the form can't be used to check which emails
  are registered.
