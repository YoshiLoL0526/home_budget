from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegisterForm, UserUpdateForm, UserProfileForm, CustomAuthForm


class CustomLoginView(LoginView):
    template_name = "login.html"
    authentication_form = CustomAuthForm

    def get_success_url(self):
        return reverse_lazy("dashboard")

    def form_invalid(self, form):
        messages.error(self.request, "Usuario o contraseña incorrectos. Por favor intente nuevamente.")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    template_name = "logout.html"
    next_page = reverse_lazy("login")


class RegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = "register.html"
    success_url = reverse_lazy("category-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get("username")
        messages.success(
            self.request,
            f"¡Cuenta creada para {username}! Ahora puedes crear tus categorías de gastos e ingresos.",
        )

        return response


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileForm(instance=request.user.userprofile)
        return render(
            request,
            "profile.html",
            {"u_form": u_form, "p_form": p_form, "page_title": "Mi Perfil"},
        )

    def post(self, request):
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = UserProfileForm(
            request.POST, request.FILES, instance=request.user.userprofile
        )
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Tu perfil ha sido actualizado correctamente")
            return redirect("profile")
        return render(
            request,
            "profile.html",
            {"u_form": u_form, "p_form": p_form, "page_title": "Mi Perfil"},
        )
