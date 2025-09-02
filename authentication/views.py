from typing import Any

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .forms import (CustomAuthenticationForm, CustomUserCreationForm,
                    UserProfileForm)
from .models import User


# Create your views here.
def register_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("tracker:index")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Реєстрація успішна!")
            return redirect("tracker:index")
        else:
            print("Form errors:", form.errors)  # Для дебагу
    else:
        form = CustomUserCreationForm()

    return render(request, "authentication/register.html", {"form": form})


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("tracker:index")

    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Вітаємо, {user.username}!")
                return redirect("tracker:index")
    else:
        form = CustomAuthenticationForm()

    return render(request, "authentication/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, "Ви вийшли з системи.")
    return redirect("tracker:index")


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    user = request.user
    assert user.is_authenticated  # для mypy

    # Отримуємо активні сесії користувача
    from tracker.models import WorkoutSession

    active_sessions = WorkoutSession.objects.filter(
        user=user, status=WorkoutSession.Status.ACTIVE
    )

    context = {
        "user": user,
        "active_sessions": active_sessions,
    }
    return render(request, "authentication/profile.html", context)


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "authentication/profile_edit.html"
    success_url = reverse_lazy("authentication:profile")

    def get_object(self, queryset: Any = None) -> User:
        user = self.request.user
        assert user.is_authenticated  # для mypy
        return user

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, "Профіль оновлено!")
        return super().form_valid(form)


# Mixins для перевірки прав доступу
class BasePermissionMixin:
    """Базовий клас для mixins перевірки прав"""

    def get_object(self) -> Any:
        raise NotImplementedError("Subclasses must implement get_object()")

    @property
    def request(self) -> HttpRequest:
        raise NotImplementedError("Subclasses must implement request property")


class UserOwnsObjectMixin(BasePermissionMixin):
    """Mixin для перевірки, чи користувач є власником об'єкта"""

    def test_func(self) -> bool:
        obj = self.get_object()
        return obj.user == self.request.user

    def handle_no_permission(self) -> HttpResponseForbidden:
        return HttpResponseForbidden("Доступ заборонено")


class UserOwnsOrAdminMixin(BasePermissionMixin):
    """Mixin для перевірки, чи користувач є власником або адміністратором"""

    def test_func(self) -> bool:
        obj = self.get_object()
        user = self.request.user
        assert user.is_authenticated  # для mypy
        return obj.user == user or user.status == User.Status.ADMIN

    def handle_no_permission(self) -> HttpResponseForbidden:
        return HttpResponseForbidden("Доступ заборонено")


class WorkoutPlanOwnerOrAdminMixin(BasePermissionMixin):
    """Mixin для перевірки, чи користувач є автором WorkoutPlan або адміністратором"""

    def test_func(self) -> bool:
        obj = self.get_object()
        user = self.request.user
        assert user.is_authenticated  # для mypy
        return obj.creator == user or user.status == User.Status.ADMIN

    def handle_no_permission(self) -> HttpResponseForbidden:
        return HttpResponseForbidden("Доступ заборонено")
