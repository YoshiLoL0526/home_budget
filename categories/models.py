from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    TYPE_CHOICES = [
        ("gasto", "Gasto"),
        ("ingreso", "Ingreso"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default="gasto", verbose_name="Tipo"
    )
    color = models.CharField(
        max_length=7, default="#3498db", verbose_name="Color"
    )  # Formato HEX (#RRGGBB)
    icon = models.CharField(max_length=50, default="fa-tag", verbose_name="Icono")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["name"]
        # Asegurar que cada usuario tenga nombres de categoría únicos
        unique_together = ["user", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
