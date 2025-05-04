from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("monthly/", views.monthly_report, name="monthly_report"),
    path("annual/", views.annual_report, name="annual_report"),
    path("export-monthly/", views.export_monthly_report, name="export_monthly_report"),
]
