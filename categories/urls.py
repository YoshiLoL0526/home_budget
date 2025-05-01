from django.urls import path
from .views import (
    CategoryListView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,
)

# Añadir a tus urlpatterns existentes
urlpatterns = [
    path("", CategoryListView.as_view(), name="category-list"),
    path("new/", CategoryCreateView.as_view(), name="category-create"),
    path(
        "<int:pk>/edit/",
        CategoryUpdateView.as_view(),
        name="category-update",
    ),
    path(
        "<int:pk>/delete/",
        CategoryDeleteView.as_view(),
        name="category-delete",
    ),
]
