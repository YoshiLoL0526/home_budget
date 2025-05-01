from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Category
from .forms import CategoryForm


class CategoryOwnershipMixin(UserPassesTestMixin):
    def test_func(self):
        category = self.get_object()
        return self.request.user == category.user


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        # Filtrar categorías por usuario actual
        return Category.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expense_categories"] = self.get_queryset().filter(type="gasto")
        context["income_categories"] = self.get_queryset().filter(type="ingreso")
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "category_form.html"
    success_url = reverse_lazy("category-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Categoría creada correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Crear Nueva Categoría"
        context["action"] = "Crear"
        return context


class CategoryUpdateView(LoginRequiredMixin, CategoryOwnershipMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "category_form.html"
    success_url = reverse_lazy("category-list")

    def form_valid(self, form):
        messages.success(self.request, "Categoría actualizada correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Editar Categoría"
        context["action"] = "Actualizar"
        return context


class CategoryDeleteView(LoginRequiredMixin, CategoryOwnershipMixin, DeleteView):
    model = Category
    template_name = "category_confirm_delete.html"
    success_url = reverse_lazy("category-list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Categoría eliminada correctamente.")
        return super().delete(request, *args, **kwargs)
