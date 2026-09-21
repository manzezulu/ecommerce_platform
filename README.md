# eCommerce Platform

A Django eCommerce app supporting two account types, **vendors**, who run
stores and list products, and **buyers**, who browse, purchase, and review
products.

## Project structure
ecommerce_platform/
├── manage.py
├── requirements.txt (Django, mysqlclient, etc.)
├── .gitignore
├── README.md
├── store/ (the "store" app)
│ ├── models.py (Store, Product, Order, OrderItem, Review, PasswordResetToken)
│ ├── forms.py
│ ├── views.py (auth, stores, products, cart/checkout, reviews, password reset)
│ ├── urls.py
│ ├── admin.py
│ ├── tests.py (automated tests)
│ ├── templatetags/store_extras.py
│ ├── migrations/
│ ├── templates/store/
│ └── static/store/styles.css
└── ecommerce_platform/ (project/core app)
├── settings.py
├── urls.py
├── asgi.py
└── wsgi.py

text

> **Not in the repository:** the `venv/` folder, `db.sqlite3`, collected
> static files under `staticfiles/`, and any `.env` file — all are
> excluded via `.gitignore` and recreated by the setup steps below.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/manzezulu/ecommerce_platform.git
cd ecommerce_platform
Replace <your-username> with your GitHub username.

2. Create and activate a virtual environment
The venv/ folder is created inside the project folder.

bash
python -m venv venv
source venv/bin/activate 
3. Install dependencies from requirements.txt
All required packages (Django, mysqlclient, and their transitive
dependencies) are listed in requirements.txt. Install them in one
command:

bash
pip install -r requirements.txt
4. Create the MySQL/MariaDB database
The project is configured to use MySQL/MariaDB via mysqlclient.
Before running migrations, create the database itself.

Log into MySQL/MariaDB as root:

bash
mysql -u root -p
Then run these SQL queries (change the password to something unique):

sql
CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ecommerce_user'@'localhost' IDENTIFIED BY 'your-password-here';
GRANT ALL PRIVILEGES ON ecommerce_db.* TO 'ecommerce_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
Open ecommerce_platform/settings.py and fill in the DATABASES block
with these credentials. The MySQL/MariaDB engine listens on port
3306 by default — do not change the port unless you have deliberately
configured a second instance elsewhere (using e.g. 3307 will cause
migrate errors).

python
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
or you can just use SQLite for a quick smoke test. Uncomment the SQLite 
lines from the settings.py

5. Apply migrations
bash
python manage.py makemigrations
python manage.py migrate
6. Collect static files
bash
python manage.py collectstatic
7. (Optional) create an admin superuser
bash
python manage.py createsuperuser
8. Run the development server
bash
python manage.py runserver
Then visit http://127.0.0.1:8000/ to browse the store, or
http://127.0.0.1:8000/admin/ to manage data through the Django
admin.

Password-reset and order-invoice emails are printed to the console by
default (see EMAIL_BACKEND in settings.py) so you can see them
without configuring a real mail server. To send real emails, uncomment
and fill in the SMTP block in settings.py.


Features implemented
Registration & roles - users register as a buyer or a vendor;
registration adds them to a matching Buyers/Vendors Django group,
which controls their permissions. Email addresses are validated as
unique (case-insensitively).

Stores & products (vendor) - vendors can create, edit, and delete
their own stores, and add/edit/delete products within them. Every
management view checks both the relevant Django permission and that
the current user actually owns the store/product.

Browsing (public) & cart (buyers only) - anyone can browse
products; only logged-in buyers can add products to a session-based
cart, view it, adjust it, and remove items. Vendors cannot access cart
or checkout functionality.

Stock-aware cart, the cart rejects additions that would exceed
the product's current stock, warns the buyer on the cart page if stock
has dropped, and aborts checkout with a clear error if any line is no
longer available (rather than silently reducing the quantity).

Checkout - creates an Order with snapshotted OrderItems,
reduces product stock, clears the cart, and emails the invoice.

Reviews - any logged-in user can review a product; a review is
automatically marked "verified" if the reviewer has an order
containing that product.

Forgotten password - a "forgot password" form emails a single-use,
time-limited (15 minute) reset link; the raw token is never stored,
only its SHA-1 hash.

Admin - every model is registered with the Django admin site.

Testing
Run the automated test suite (registration, unique-email enforcement,
group permissions & ownership checks, buyer-only cart access, stock
enforcement, cart/checkout, invoice emailing, reviews, and password
reset):

bash
python manage.py test store

Planning
See the Planning/ folder for the requirements.

Notes
The venv/ folder has been excluded from this submission.

MySQL/MariaDB runs on port 3306 by default