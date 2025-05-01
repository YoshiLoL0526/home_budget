from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum
from categories.models import Category
from .models import Operation
from .forms import OperationForm


class OperationListView(LoginRequiredMixin, ListView):
    model = Operation
    paginate_by = 10
    template_name = "operation_list.html"

    def get_queryset(self):
        queryset = Operation.objects.filter(user=self.request.user)

        # Aplicar filtros
        category_id = self.request.GET.get("category")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        # Separar gastos e ingresos basados en el tipo de categoría
        expenses_total = (
            queryset.filter(category__type="gasto").aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )
        income_total = (
            queryset.filter(category__type="ingreso").aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )

        # Agregar resúmenes al contexto
        context["expenses_total"] = expenses_total
        context["income_total"] = income_total
        context["net_total"] = income_total - expenses_total

        # Obtener categorías para el filtro
        context["categories"] = Category.objects.filter(user=self.request.user)

        # Filtros actuales para mantener estado en la UI
        context["current_filters"] = {
            "category": self.request.GET.get("category", ""),
            "start_date": self.request.GET.get("start_date", ""),
            "end_date": self.request.GET.get("end_date", ""),
        }

        return context


class OperationDetailView(LoginRequiredMixin, DetailView):
    model = Operation
    template_name = "operation_detail.html"

    def get_queryset(self):
        return Operation.objects.filter(user=self.request.user)


class OperationCreateView(LoginRequiredMixin, CreateView):
    model = Operation
    form_class = OperationForm
    template_name = "operation_form.html"
    success_url = reverse_lazy("operation-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class OperationUpdateView(LoginRequiredMixin, UpdateView):
    model = Operation
    form_class = OperationForm
    template_name = "operation_form.html"
    success_url = reverse_lazy("operation-list")

    def get_queryset(self):
        return Operation.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class OperationDeleteView(LoginRequiredMixin, DeleteView):
    model = Operation
    template_name = "operation_confirm_delete.html"
    success_url = reverse_lazy("operation-list")

    def get_queryset(self):
        return Operation.objects.filter(user=self.request.user)
