# UI Layout — eCommerce Platform

## Site structure

```
Header (all pages)
├── Site title / logo → links to product list
├── "Browse" link
├── If logged in: "Cart", "My Stores" (vendors only), username, "Log out"
└── If logged out: "Log in", "Register"

Main content (varies per page — see below)

Footer (all pages) — site name
```

## Page-by-page layout

**Product list (`/`)** — a responsive grid of product cards. Each card
shows the product name, its store, price, and stock status, and links to
the product detail page. This is the landing page for every visitor.

**Product detail (`/product/<id>/`)** — a single card with the product's
full description, price, and stock. Below it:
- An "Add to cart" form (quantity + button) if logged in and in stock.
- Owner-only "Edit product" / "Delete product" buttons if the current
  user owns the store.
- A reviews section: existing reviews (each tagged "Verified purchase" or
  "Unverified"), followed by a review form for any logged-in user.

**Cart (`/cart/`)** — a table of product / quantity / line total rows,
a running total, and a "Checkout" button. Each row has a "Remove" link.

**Order detail / invoice (`/orders/<id>/`)** — shown right after
checkout: a table of the items purchased, quantities, unit price, and
total, with a note that a copy was emailed.

**My stores (`/stores/mine/`, vendor only)** — a simple list of the
vendor's stores with a "+ New store" button.

**Store detail (`/stores/<id>/`)** — the store's name/description, then
a product grid identical in style to the main product list, scoped to
that store. Owners additionally see "Edit store" / "Delete store" and
"+ Add product" controls.

**Forms (register, login, forgot/reset password, store form, product
form)** — a single centred card (`.form-card`) with stacked label/input
pairs and one primary submit button, kept deliberately simple and
consistent across every form in the app.

## Design language

- A dark header bar (`#1b1f27`) against a light page background
  (`#f5f6f8`), with a single accent colour (`#3a7cff`) used for primary
  buttons, links, and prices — enough to draw the eye to price tags and
  calls to action without the page feeling busy.
- Cards (`.product-card`, `.form-card`) share the same white background,
  1px border, and rounded corners throughout, so product grids, forms,
  and store listings all read as part of one consistent system.
- Flash messages (success/error) render as a coloured strip directly
  under the header, so feedback from an action (e.g. "Added to cart",
  "You do not have permission…") is always in the same place.
