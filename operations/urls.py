from django.urls import path
from . import views

urlpatterns = [
    path("", views.OperationListView.as_view(), name="operation-list"),
    path("create/", views.OperationCreateView.as_view(), name="operation-create"),
    path("<int:pk>/", views.OperationDetailView.as_view(), name="operation-detail"),
    path("<int:pk>/update/", views.OperationUpdateView.as_view(), name="operation-update"),
    path("<int:pk>/delete/", views.OperationDeleteView.as_view(), name="operation-delete"),
]
