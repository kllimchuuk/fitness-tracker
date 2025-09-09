import logging
import re

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect

from tracker.models import User

logger = logging.getLogger(__name__)


@csrf_protect
def register_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        age = request.POST.get("age")
        height = request.POST.get("height")
        goal = request.POST.get("goal", "").strip()

        if not username or len(username) < 3:
            return render(
                request,
                "register.html",
                {"error": "Username must be at least 3 characters"},
            )

        if not email:
            return render(request, "register.html", {"error": "Email is required"})

        email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
        if not re.match(email_pattern, email):
            return render(request, "register.html", {"error": "Invalid email format"})

        if len(password) < 8:
            return render(
                request,
                "register.html",
                {"error": "Password must be at least 8 characters"},
            )

        if User.objects.filter(username=username).exists():
            return render(
                request, "register.html", {"error": "Username already exists"}
            )

        if User.objects.filter(email=email).exists():
            return render(request, "register.html", {"error": "Email already exists"})

        try:
            user = User(username=username, email=email)
            user.password = make_password(password)
            user.status = User.Status.CUSTOMER

            if age:
                try:
                    user.age = int(age)
                    if user.age < 1 or user.age > 120:
                        raise ValueError("Invalid age")
                except ValueError:
                    return render(request, "register.html", {"error": "Invalid age"})

            if height:
                try:
                    user.height = float(height)
                    if user.height < 50 or user.height > 300:
                        raise ValueError("Invalid height")
                except ValueError:
                    return render(request, "register.html", {"error": "Invalid height"})

            if goal:
                user.goal = goal[:256]

            user.save()

            request.session.cycle_key()
            request.session["user_id"] = user.id
            request.session["username"] = username

            logger.info(f"New user registered: {username} ({email})")
            return redirect("/")

        except Exception as e:
            logger.error(f"Registration error: {e}")
            return render(
                request,
                "register.html",
                {"error": "Registration failed. Please try again."},
            )

    return render(request, "register.html")


@csrf_protect
def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        try:
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                request.session.cycle_key()
                request.session["user_id"] = user.id
                request.session["username"] = username

                logger.info(f"User logged in: {username}")
                return redirect("/")
            else:
                logger.warning(f"Failed login attempt for user: {username}")
                return render(request, "login.html", {"error": "Invalid credentials"})
        except User.DoesNotExist:
            logger.warning(f"Login attempt for non-existent user: {username}")
            return render(request, "login.html", {"error": "Invalid credentials"})

    return render(request, "login.html")


@csrf_protect
def logout_view(request: HttpRequest) -> HttpResponse:
    username = request.session.get("username", "Unknown")
    request.session.flush()
    logger.info(f"User logged out: {username}")
    return redirect("/authentication/login/")
