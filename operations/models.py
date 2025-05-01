from django.db import models
from django.contrib.auth.models import User
from categories.models import Category
from django.urls import reverse


class Operation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="operations")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="operations"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.date})"

    def get_absolute_url(self):
        return reverse("operation-detail", kwargs={"pk": self.pk})
