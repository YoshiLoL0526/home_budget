from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import UserProfile
import pytz


class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Nombre de usuario")}
        ),
        label=_("Usuario")
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": _("Contraseña")}
        ),
        label=_("Contraseña")
    )


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Nombre de usuario")}
        ),
        label=_("Usuario")
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": _("correo@ejemplo.com")}
        ),
        label=_("Correo electrónico")
    )
    password1 = forms.CharField(
        label=_("Contraseña"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": _("Contraseña")}
        ),
    )
    password2 = forms.CharField(
        label=_("Confirmar contraseña"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": _("Confirmar contraseña")}
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label=_("Usuario")
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        label=_("Correo electrónico")
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label=_("Nombre")
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label=_("Apellidos")
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]


class UserProfileForm(forms.ModelForm):
    timezone = forms.ChoiceField(
        choices=[(tz, tz) for tz in pytz.common_timezones],
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Zona horaria")
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control"}),
        label=_("Foto de perfil")
    )
    monthly_budget = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label=_("Presupuesto mensual")
    )
    currency = forms.ChoiceField(
        choices=[
            ("EUR", _("Euro (€)")),
            ("USD", _("Dólar Estadounidense ($)")),
            ("GBP", _("Libra Esterlina (£)")),
            ("MXN", _("Peso Mexicano ($)")),
            ("BRL", _("Real Brasileño (R$)")),
            ("CUP", _("Peso Cubano (₱)")),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Moneda")
    )

    class Meta:
        model = UserProfile
        fields = ["timezone", "profile_picture", "monthly_budget", "currency"]
