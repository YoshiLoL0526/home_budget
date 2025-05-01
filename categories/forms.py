from django import forms
from .models import Category


class CategoryForm(forms.ModelForm):
    ICON_CHOICES = [
        ("fa-solid fa-house", "Casa"),
        ("fa-solid fa-utensils", "Comida"),
        ("fa-solid fa-car", "Transporte"),
        ("fa-solid fa-film", "Entretenimiento"),
        ("fa-solid fa-cart-shopping", "Compras"),
        ("fa-solid fa-credit-card", "Tarjeta de Crédito"),
        ("fa-solid fa-money-bill", "Efectivo"),
        ("fa-solid fa-briefcase", "Trabajo"),
        ("fa-solid fa-graduation-cap", "Educación"),
        ("fa-solid fa-kit-medical", "Salud"),
        ("fa-solid fa-plane", "Viajes"),
        ("fa-solid fa-gift", "Regalos"),
        ("fa-solid fa-gamepad", "Ocio"),
        ("fa-solid fa-shirt", "Ropa"),
        ("fa-solid fa-dumbbell", "Deporte"),
        ("fa-solid fa-wifi", "Internet"),
        ("fa-solid fa-mobile-screen", "Teléfono"),
        ("fa-solid fa-plug", "Servicios"),
        ("fa-solid fa-coins", "Inversiones"),
        ("fa-solid fa-piggy-bank", "Ahorros"),
        ("fa-solid fa-hand-holding-dollar", "Préstamos"),
        ("fa-solid fa-tag", "Otros"),
    ]

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nombre de la categoría"}
        )
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Descripción breve de la categoría",
            }
        ),
    )
    type = forms.ChoiceField(
        choices=Category.TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    color = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control color-picker", "type": "color"}
        )
    )
    icon = forms.ChoiceField(
        choices=ICON_CHOICES,
        widget=forms.Select(attrs={"class": "form-select icon-select"}),
    )

    class Meta:
        model = Category
        fields = ["name", "description", "type", "color", "icon"]
