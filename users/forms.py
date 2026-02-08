from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации пользователя."""

    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": _("Email")}),
    )
    username = forms.CharField(
        label=_("Username"),
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("Username")}),
    )
    password1 = forms.CharField(
        label=_("Password"), widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": _("Password")})
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": _("Confirm password")}),
    )

    class Meta:
        model = User
        fields = ("email", "username", "password1", "password2")


class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа пользователя."""

    username = forms.EmailField(
        label=_("Email"), widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": _("Email")})
    )
    password = forms.CharField(
        label=_("Password"), widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": _("Password")})
    )


class CustomPasswordResetForm(PasswordResetForm):
    """Форма восстановления пароля."""

    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": _("Email")}),
    )


class CustomSetPasswordForm(SetPasswordForm):
    """Форма установки нового пароля."""

    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": _("New password")}),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": _("Confirm new password")}),
    )
