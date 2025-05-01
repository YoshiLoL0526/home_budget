from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import pytz


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timezone = models.CharField(
        max_length=50, default="UTC", choices=[(tz, tz) for tz in pytz.common_timezones]
    )
    profile_picture = models.ImageField(
        upload_to="profile_pics", blank=True
    )
    monthly_budget = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(
        max_length=3,
        default="BRL",
        choices=[
            ("EUR", "Euro (€)"),
            ("USD", "Dólar Estadounidense ($)"),
            ("GBP", "Libra Esterlina (£)"),
            ("MXN", "Peso Mexicano ($)"),
            ("BRL", "Real Brasileño (R$)"),
            ("CUP", "Peso Cubano (₱)"),
        ],
    )

    def __str__(self):
        return f"Perfil de {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
