"""
Django settings for the ecommerce_platform project.

This file configures the database, email backend, and installed apps.
SQLite is used by default for quick local testing; a commented MySQL/
MariaDB block is provided for switching to a production-style database.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security ------------------------------------------------------------
# NOTE: replace SECRET_KEY with a value loaded from the environment
# before deploying anywhere other than local development.
SECRET_KEY = "django-insecure-CHANGE-ME-before-deploying"

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


# --- Applications --------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "store",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ecommerce_platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ecommerce_platform.wsgi.application"


# --- Database ------------------------------------------------------------
# SQLite is used by default. To use MariaDB, comment out the SQLite
# block below, uncomment the MySQL block, and fill in your credentials.

#DATABASES = {
 #   "default": {
  #      "ENGINE": "django.db.backends.sqlite3",
   #     "NAME": BASE_DIR / "db.sqlite3",
    #}
#}
DATABASES = {
         "default": {
         "ENGINE": "django.db.backends.mysql",
         "NAME": "ecommerse_db",
         "USER": "ecom_user",
         "PASSWORD": "123Rain@3",
         "HOST": "127.0.0.1",
         "PORT": "3306",   # default MySQL/MariaDB port
     }
 }


# --- Password validation -------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Internationalisation ------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = True
USE_TZ = True


# --- Static files --------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Email ---------------------------------------------------------------
# For Practical purposesnemails are printed to the console so you can see the
# invoice and password-reset links without a mail server. Running the
# server and performing a checkout will print the invoice there.

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@starbridge-market.local"

# --- Email (production) --------------------------------------------------
# Uncomment and fill in to send real emails.
#
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = "yourcompanyaddress@gmail.com"
# EMAIL_HOST_PASSWORD = "ecommercepassword"
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# --- Authentication redirects -------------------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "product_list"
LOGOUT_REDIRECT_URL = "login"