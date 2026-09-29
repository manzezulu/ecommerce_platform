# Django eCommerce Platform

A Django eCommerce application where vendors can create stores and manage products, while buyers can browse products, add items to a cart, place orders, and leave reviews.

The project also provides a **RESTful API** for stores, products, and reviews. It also integrates with the **GitHub Events API** as a third-party data source to display recent public activity.

## Project Structure

```text
ecommerce_platform/
├── manage.py
├── requirements.txt
├── .gitignore
├── README.md
│
├── docs/
│   └── sequence_diagram.png
│
├── store/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── api_views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   ├── migrations/
│   │
│   ├── functions/
│   │   ├── __init__.py
│   │   └── reddit.py
│   │
│   ├── templates/
│   │   └── store/
│   │       ├── base.html
│   │       ├── reddit_feed.html
│   │       └── ... other templates
│   │
│   ├── static/
│   │   └── store/
│   │       └── styles.css
│   │
│   └── templatetags/
│       └── store_extras.py
│
└── ecommerce_platform/
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    └── wsgi.py
```

The following files and directories are not included in the repository:

```text
venv/
db.sqlite3
staticfiles/
.env
```

These files are excluded using `.gitignore`.

---

## Features

### User Registration

Users can register as either:

- Buyer
- Vendor

Users are automatically added to the appropriate Django group during registration.

Email addresses must be unique.

### Vendors

Vendors can:

- Create their own store
- Edit their store
- Delete their store
- Add products
- Edit their products
- Delete their products

A vendor can only manage their own store and products.

### Buyers

Buyers can:

- Browse products
- Add products to their cart
- Change product quantities
- Remove products from their cart
- Checkout
- Leave product reviews

Vendors cannot access buyer cart and checkout functionality.

### Shopping Cart

The shopping cart uses Django sessions.

The cart checks product stock when items are added.

If stock changes after an item has been added to the cart, the buyer is warned before checkout.

Checkout will not continue if the requested quantity is no longer available.

### Orders

When a buyer checks out:

1. An order is created.
2. Order items are created.
3. Product stock is reduced.
4. The cart is cleared.
5. An invoice email is generated.

The order keeps the relevant product and price information from the time of purchase.

### Reviews

Logged-in users can review products.

A review is marked as verified when the user has previously purchased the product.

### Password Reset

Users can request a password reset.

The reset link:

- Is sent by email.
- Expires after 15 minutes.
- Can only be used once.

The reset token is stored as a hash rather than the original token.

### Django Admin

The application's models are registered with Django Admin.

---

## REST API

The project exposes a RESTful API built with the **Django REST Framework (DRF)**.

The API supports both **JSON and XML** content negotiation.

Read endpoints are publicly accessible.

Write endpoints require authentication using **HTTP Basic Authentication**. Session authentication is also available when using the DRF browsable API in a browser.

Ownership rules are enforced for vendor operations. Vendors can only create stores for themselves and can only add products to stores they own.

### API Endpoints

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| GET | `/api/stores/` | No | List all stores with products |
| POST | `/api/stores/` | Yes - Vendor | Create a new store |
| GET | `/api/stores/<id>/` | No | Retrieve a single store |
| GET | `/api/stores/<id>/products/` | No | List products in a store |
| POST | `/api/stores/<id>/products/` | Yes - Owner | Add a product to a store |
| GET | `/api/products/<id>/` | No | Retrieve a single product |
| GET | `/api/products/<id>/reviews/` | No | List reviews for a product |
| GET | `/api/stores.xml/` | No | Retrieve store list as XML |

### Example: Create a Store

A vendor can create a store using HTTP Basic Authentication:

```bash
curl -u vendor_username:vendor_password \
     -X POST http://127.0.0.1:8000/api/stores/ \
     -H "Content-Type: application/json" \
     -d '{"name": "My API Store", "description": "Created via the API"}'
```

### Example: Add a Product

A vendor can add a product to their own store:

```bash
curl -u vendor_username:vendor_password \
     -X POST http://127.0.0.1:8000/api/stores/1/products/ \
     -H "Content-Type: application/json" \
     -d '{"name": "API Widget", "description": "From the API", "price": "12.50", "stock": 10}'
```

Attempting to add a product to another vendor's store returns:

```text
403 Forbidden
```

The DRF browsable API is available through the GET endpoints, making it possible to explore the API directly from a browser.

---

## Third-Party API - GitHub Events

The project integrates with the **GitHub Events API** to display recent public activity on GitHub.

Visit:

```text
/reddit/
```

to view recent GitHub events.

The API integration is handled by:

```text
store/functions/reddit.py
```

The helper function:

1. Sends a GET request to the external API.
2. Provides a descriptive `User-Agent`.
3. Parses the JSON response.
4. Extracts the relevant event information.
5. Displays the event title, actor, and repository link.

### Why GitHub Instead of Reddit?

The original task suggested using Reddit's public JSON endpoints.

During development, it was found that Reddit's anonymous `.json` and `.rss` feeds are no longer suitable for this implementation without OAuth authentication.

To keep the third-party API integration functional without requiring OAuth credentials, the project uses GitHub's public Events API instead.

The integration follows the same general pattern:

```text
Application
     |
     v
Third-Party API
     |
     v
JSON Response
     |
     v
Data Processing
     |
     v
Django Template
```

The data source can be changed in the future by updating the API call in:

```text
store/views.py
```

For example:

```python
posts = get_reddit_posts("github")
```

---

## Technologies Used

- Python
- Django
- Django REST Framework
- djangorestframework-xml
- Requests
- Certifi
- MySQL / MariaDB
- SQLite
- HTML
- CSS
- Django Templates
- Git

SQLite can also be used for quick local testing.

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/manzezulu/ecommerce_platform.git
cd ecommerce_platform
```

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Database Setup

### 4. Create the MySQL Database

Log into MySQL or MariaDB:

```bash
mysql -u root -p
```

Create the database:

```sql
CREATE DATABASE ecommerce_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

Create the database user:

```sql
CREATE USER 'ecommerce_user'@'localhost'
IDENTIFIED BY 'your-password-here';
```

Grant the user access to the database:

```sql
GRANT ALL PRIVILEGES
ON ecommerce_db.*
TO 'ecommerce_user'@'localhost';

FLUSH PRIVILEGES;
```

Exit MySQL:

```sql
EXIT;
```

---

## Configure the Database

### 5. Update Django Settings

Open:

```text
ecommerce_platform/settings.py
```

Update the database configuration:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "ecommerce_db",
        "USER": "ecommerce_user",
        "PASSWORD": "your-password-here",
        "HOST": "127.0.0.1",
        "PORT": "3306",
    }
}
```

MySQL and MariaDB normally use port `3306`.

---

## Run the Application

### 6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create an Admin User

```bash
python manage.py createsuperuser
```

Follow the instructions displayed in the terminal.

### 8. Start the Development Server

```bash
python manage.py runserver
```

Open the application in your browser:

```text
http://127.0.0.1:8000/
```

Django Admin:

```text
http://127.0.0.1:8000/admin/
```

---

## Email Configuration

For development, password reset emails and order invoices are printed in the terminal instead of being sent through a real email service.

A real SMTP email service can be configured in `settings.py` if required.

---

## Testing

The project includes automated tests covering the main functionality.

Run the test suite with:

```bash
python manage.py test store
```

The tests cover:

- User registration
- Unique email addresses
- User groups and permissions
- Store ownership
- Product ownership
- Buyer-only cart access
- Stock checking
- Cart functionality
- Checkout
- Orders
- Invoice emails
- Product reviews
- Password reset

---

## API Testing

The REST API can be tested using tools such as **Postman**.

For authenticated requests, use **HTTP Basic Authentication** with a vendor's username and password.

Example:

```text
Authentication Type: Basic Auth

Username: vendor_username
Password: vendor_password
```

---

## SSL Certificates

If an SSL certificate error occurs when making requests to an external API, such as:

```text
SSLCertVerificationError
```

install or upgrade `certifi`:

```bash
pip install --upgrade certifi
```

The certificate bundle can then be explicitly provided to `requests`:

```python
import certifi
import requests

response = requests.get(
    url,
    headers=headers,
    verify=certifi.where()
)
```

The helper in:

```text
store/functions/reddit.py
```

already uses this approach.

---

## Planning

Project requirements and planning documents are available in the:

```text
Planning/
```

directory.

The project also includes a sequence diagram:

```text
docs/sequence_diagram.png
```

---

## Author

**Manzezulu Mazibuko**

GitHub:  
https://github.com/manzezulu

LinkedIn:  
https://www.linkedin.com/in/manzezulu-mazibuko-b62a26177/
