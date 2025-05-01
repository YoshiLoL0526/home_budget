from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("monthly/", views.monthly_report, name="monthly_report"),
    path("annual/", views.annual_report, name="annual_report"),
    path("save/", views.save_report, name="save_report"),
    path("saved/", views.SavedReportListView.as_view(), name="saved_reports"),
]
