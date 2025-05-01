from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class SavedReport(models.Model):
    REPORT_TYPES = [
        ("weekly", _("Weekly")),
        ("monthly", _("Monthly")),
        ("annual", _("Annual")),
        ("custom", _("Custom")),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved_reports"
    )
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Parámetros de filtro guardados en formato JSON
    filters = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Saved Report")
        verbose_name_plural = _("Saved Reports")

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
