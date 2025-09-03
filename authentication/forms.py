from typing import Any

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    age = forms.IntegerField(required=False, min_value=1, max_value=120)
    height = forms.FloatField(required=False, min_value=0.5, max_value=3.0)
    goal = forms.CharField(
        required=False, max_length=256, widget=forms.Textarea(attrs={"rows": 3})
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "age",
            "height",
            "goal",
        )

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Цей email вже використовується.")
        return email or ""

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.age = self.cleaned_data.get("age")
        user.height = self.cleaned_data.get("height")
        user.goal = self.cleaned_data.get("goal")
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Username або Email",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def clean(self) -> dict[str, Any]:
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            # Спробуємо автентифікуватися за username або email
            user = authenticate(username=username, password=password)
            if user is None:
                # Якщо не спрацювало, спробуємо знайти користувача за email
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is None:
                raise forms.ValidationError("Невірний username/email або пароль.")

            self.user_cache = user
        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "age", "height", "goal")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "age": forms.NumberInput(attrs={"class": "form-control"}),
            "height": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "goal": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
