# store/forms.py
"""
Forms for the store app.

All forms live here so views stay thin and validation rules are easy to
find in one place. Custom `clean_*` methods surface friendly error
messages to the user.
"""

from django import forms
from django.contrib.auth.models import User

from .models import Store, Product, Review


class RegisterForm(forms.Form):
    """Register a new account as either a buyer or a vendor.

    Fields:
    - username: unique login name.
    - email: unique email address (validated case-insensitively).
    - password / password_confirm: must match.
    - account_type: "buyer" or "vendor" — determines group membership.
    """

    ACCOUNT_TYPE_CHOICES = [
        ("buyer", "Buyer"),
        ("vendor", "Vendor"),
    ]

    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPE_CHOICES)

    def clean_username(self):
        """Reject usernames that are already taken."""
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        """Reject emails that are already registered.

        Case-insensitive so 'Alice@Example.com' and 'alice@example.com'
        are treated as the same address — otherwise invoice emailing
        and password resets become ambiguous.
        """
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        """Ensure the two password fields match."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class LoginForm(forms.Form):
    """Username/password form for the login view."""

    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class ForgotPasswordForm(forms.Form):
    """Collects an email address for the password-reset flow."""

    email = forms.EmailField()


class SetNewPasswordForm(forms.Form):
    """Collects and confirms the new password chosen during reset."""

    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        """Ensure the two password fields match."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class StoreForm(forms.ModelForm):
    """Create or edit a Store (name + description)."""

    class Meta:
        model = Store
        fields = ["name", "description"]


class ProductForm(forms.ModelForm):
    """Create or edit a Product (name, description, price, stock)."""

    class Meta:
        model = Product
        fields = ["name", "description", "price", "stock"]


class ReviewForm(forms.ModelForm):
    """Submit a rating (1–5) and an optional comment for a product."""

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(i, i) for i in range(1, 6)]),
        }


class AddToCartForm(forms.Form):
    """Ask for the quantity to add.

    Only the lower bound is enforced here; the view checks the upper
    bound against the product's current stock so the error message can
    name the product and the remaining quantity.
    """

    quantity = forms.IntegerField(min_value=1, initial=1)