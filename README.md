# Django eCommerce Platform

A Django eCommerce application where vendors can create stores and manage
products, while buyers can browse products, add items to a cart, place
orders, and leave reviews.

The project also exposes a **RESTful API** for stores, products, and
reviews, and integrates with the **GitHub Events API** as a third-party
data source to display recent public activity.

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
│   ├── api_views.py            # REST API views
│   ├── serializers.py          # DRF serializers
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   ├── migrations/
│   ├── functions/
│   │   ├── __init__.py
│   │   └── reddit.py           # Third-party API helper (GitHub)
│   ├── templates/
│   │   └── store/
│   │       ├── base.html
│   │       ├── reddit_feed.html
│   │       └── ... (other templates)
│   ├── static/
│   │   └── store/
│   │       └── styles.css
│   └── templatetags/
│       └── store_extras.py
│
└── ecommerce_platform/
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    └── wsgi.py
```

The following files are not included in the repository:

```text
venv/
db.sqlite3
staticfiles/
.env
```

These files are excluded using `.gitignore`.

## Features

### User Registration

Users can register as either:

- Buyer
- Vendor

Users are added to the appropriate Django group during registration.

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
- Change quantities
- Remove products from their cart
- Checkout
- Leave product reviews

Vendors cannot access the buyer cart and checkout functionality.

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

The order keeps the relevant product and price information at the time of purchase.

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

### REST API
The project exposes a RESTful API built with the Django REST
Framework (DRF). The API supports both JSON and XML content
negotiation.

Read endpoints are public. Write endpoints require
authentication using HTTP Basic Auth (or session auth when
accessing the DRF browsable API in the browser) and enforce
ownership rules - vendors can only create stores for themselves
and only add products to their own stores.

### API Endpoints
Method	URL	Auth	Purpose
GET	/api/stores/	No	List all stores (with products)
POST	/api/stores/	Yes (vendor)	Create a new store
GET	/api/stores/<id>/	No	Retrieve one store
GET	/api/stores/<id>/products/	No	List products in a store
POST	/api/stores/<id>/products/	Yes (owner)	Add a product to a store
GET	/api/products/<id>/	No	Retrieve one product
GET	/api/products/<id>/reviews/	No	List reviews for a product
GET	/api/stores.xml/	No	Store list rendered as XML
Example: create a store (Basic Auth)
bash
curl -u vendor_username:vendor_password \
     -X POST http://127.0.0.1:8000/api/stores/ \
     -H "Content-Type: application/json" \
     -d '{"name": "My API Store", "description": "Created via the API"}'
Example: add a product to your own store
bash
curl -u vendor_username:vendor_password \
     -X POST http://127.0.0.1:8000/api/stores/1/products/ \
     -H "Content-Type: application/json" \
     -d '{"name": "API Widget", "description": "From the API",
          "price": "12.50", "stock": 10}'
Attempting to add a product to someone else's store returns
403 Forbidden.

The DRF browsable API is available at any of the GET endpoints,
which makes it easy to explore the API from a browser.

### Third-Party API - GitHub Events Feed
The project integrates with the GitHub Events API to display
recent public activity on GitHub.

Visit /reddit/ to see recent GitHub events.

Data is fetched by a helper function in store/functions/reddit.py.

The helper sends a GET request with a descriptive User-Agent
and parses the JSON response.

Only the event title, actor, and a link to the repository are
displayed.

### Discovered during development 
The task originally suggested using
Reddit's public JSON endpoints. However i came accross an article that states, 
as of 2026 Reddit has closed anonymous access to both its .json and .rss feeds, 
returning HTTP 403 unless an OAuth token is supplied. To keep the
third-party-integration exercise functional without requiring OAuth
credentials, I used GitHub's public Events API,
which follows the exact same pattern.

To change the data source in future, edit the call in
store/views.py:

python
posts = get_reddit_posts("github")

## Technologies Used

- Python
- Django
- Django REST Framework
- djangorestframework-xml
- Requests (for third party API calls)
- Certifi (for SSL certificate verification)
- MySQL / MariaDB
- HTML
- CSS
- Django Templates
- Git

SQLite can also be used for a quick local test.

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/manzezulu/ecommerce_platform.git
cd ecommerce_platform
```

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Create the MySQL Database

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

Give the user access to the database:

```sql
GRANT ALL PRIVILEGES
ON ecommerce_db.*
TO 'ecommerce_user'@'localhost';

FLUSH PRIVILEGES;
```

Then exit:

```sql
EXIT;
```

## 5. Configure the Database

Open:

```text
ecommerce_platform/settings.py
```

Update the database settings:

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

MySQL/MariaDB normally uses port `3306`.

## 6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 7. Create an Admin User

```bash
python manage.py createsuperuser
```

Follow the instructions in the terminal.

## 8. Run the Application

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

## Email

For development, password reset emails and order invoices are printed in the terminal instead of being sent through a real email service.

A real SMTP email service can be configured in `settings.py` if required.

## Testing

The project includes automated tests for the main functionality.

Run the tests with:

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

### API Testing
The API endpoints can be tested with:

Postman - recommended for authenticated POST requests.

For authenticated requests, use HTTP Basic Auth with a vendor's
username and password.

SSL / Certificates
If requests raises SSLCertVerificationError when calling external
APIs, install/upgrade certifi and pass its bundle explicitly:

python
import certifi
import requests

response = requests.get(url, headers=headers, verify=certifi.where())
The helper in store/functions/reddit.py already does this.

## Planning

Project requirements and planning documents are available in the `Planning/` folder.

## Author

Manzezulu Mazibuko

GitHub: https://github.com/manzezulu

LinkedIn: https://www.linkedin.com/in/manzezulu-mazibuko-b62a26177/
