import logging
import re

from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth import password_validation
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .models import User

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
AGE_MIN, AGE_MAX = 1, 120
HEIGHT_MIN, HEIGHT_MAX = 50.0, 300.0
GOAL_MAX_LEN = 256
logger = logging.getLogger(__name__)


def validate_email(email: str, check_exists: bool = True) -> str:
    email = User.objects.normalize_email((email or "").strip())
    if not email:
        raise ValidationError("Email is required")
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Invalid email format")
    if check_exists and User.objects.filter(email__iexact=email).exists():
        raise ValidationError("Email already exists")
    return email


def validate_password(password: str, user: User | None = None) -> str:
    try:
        password_validation.validate_password(password, user)
    except ValidationError as e:
        raise ValidationError(" ".join(e.messages))
    return password


def validate_age(age: str) -> int:
    if not age:
        raise ValidationError("Age is required")
    try:
        age_int = int(age)
        if age_int < AGE_MIN or age_int > AGE_MAX:
            raise ValidationError("Invalid age")
        return age_int
    except ValueError:
        raise ValidationError("Invalid age")


def validate_height(height: str) -> float:
    if not height:
        raise ValidationError("Height is required")
    try:
        height_float = float(height)
        if height_float < HEIGHT_MIN or height_float > HEIGHT_MAX:
            raise ValidationError("Invalid height")
        return height_float
    except ValueError:
        raise ValidationError("Invalid height")


def validate_goal(goal: str) -> str:
    goal = (goal or "").strip()
    if not goal:
        raise ValidationError("Goal is required")
    if len(goal) > GOAL_MAX_LEN:
        raise ValidationError(f"Goal must be {GOAL_MAX_LEN} characters or less")
    return goal


def create_and_save_user(email: str, password: str, age: int, height: float, goal: str) -> User:
    return User.objects.create_user(
        email=email,
        password=password,
        status=User.Status.CUSTOMER,
        age=age,
        height=height,
        goal=goal,
    )


def redirect_after_login(request: HttpRequest) -> HttpResponse:
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("/")


def render_error(request: HttpRequest, error_message: str) -> HttpResponse:
    return render(request, "register.html", {"error": error_message})


@csrf_protect
def register_view(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return render(request, "register.html")

    email = request.POST.get("email", "")
    password = request.POST.get("password", "")
    age = request.POST.get("age", "")
    height = request.POST.get("height", "")
    goal = request.POST.get("goal", "")

    try:
        validated_email = validate_email(email)
    except ValidationError as e:
        return render_error(request, str(e))

    try:
        validated_password = validate_password(password)
    except ValidationError as e:
        return render_error(request, str(e))

    try:
        age_int = validate_age(age)
    except ValidationError as e:
        return render_error(request, str(e))

    try:
        height_float = validate_height(height)
    except ValidationError as e:
        return render_error(request, str(e))

    try:
        goal_str = validate_goal(goal)
    except ValidationError as e:
        return render_error(request, str(e))

    try:
        user = create_and_save_user(validated_email, validated_password, age_int, height_float, goal_str)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return render_error(request, "Registration failed. Please try again.")

    login(request, user)
    logger.info(f"New user registered: {validated_email}")
    return redirect("/")


@csrf_protect
def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        email = request.POST.get("email", "")
        password = request.POST.get("password", "")

        if not email or not password:
            return render(request, "login.html", {"error": "Invalid credentials"})

        try:
            validated_email = validate_email(email, check_exists=False)
        except ValidationError:
            return render(request, "login.html", {"error": "Invalid credentials"})

        user = authenticate(request, username=validated_email, password=password)
        if user is None:
            logger.warning(f"Failed login attempt for: {validated_email}")
            return render(request, "login.html", {"error": "Invalid credentials"})

        login(request, user)
        logger.info(f"User logged in: {validated_email}")
        return redirect_after_login(request)

    return render(request, "login.html")


@require_POST
@csrf_protect
def logout_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        logger.info(f"User logged out: {request.user.email}")
    logout(request)
    return redirect("authentication:login")


@login_required
@csrf_protect
def profile_view(request: HttpRequest) -> HttpResponse:
    user = request.user

    return render(
        request,
        "profile.html",
        {
            "email": user.email,
            "status": user.status,
            "age": user.age,
            "height": user.height,
            "goal": user.goal,
        },
    )


@login_required
@csrf_protect
def profile_edit_view(request: HttpRequest) -> HttpResponse:
    user = request.user

    if request.method != "POST":
        return render(request, "profile_edit.html", {"user": user})

    age = request.POST.get("age", "")
    height = request.POST.get("height", "")
    goal = request.POST.get("goal", "")

    if age:
        try:
            user.age = validate_age(age)
        except ValidationError as e:
            return render(request, "profile_edit.html", {"user": user, "error": str(e)})

    if height:
        try:
            user.height = validate_height(height)
        except ValidationError as e:
            return render(request, "profile_edit.html", {"user": user, "error": str(e)})

    if goal:
        try:
            user.goal = validate_goal(goal)
        except ValidationError as e:
            return render(request, "profile_edit.html", {"user": user, "error": str(e)})

    user.save()
    logger.info(f"User profile updated: {user.email}")
    return redirect("/authentication/profile/")


@login_required
@csrf_protect
def change_password_view(request: HttpRequest) -> HttpResponse:
    user = request.user

    if request.method != "POST":
        return render(request, "profile_password.html")

    current = request.POST.get("current_password", "")
    new = request.POST.get("new_password", "")

    if not user.check_password(current):
        return render(request, "profile_password.html", {"error": "Incorrect current password"})

    try:
        validate_password(new, user)
    except ValidationError as e:
        return render(request, "profile_password.html", {"error": str(e)})

    if current == new:
        return render(
            request,
            "profile_password.html",
            {"error": "The new password matches the old one"},
        )

    user.set_password(new)
    user.save()
    update_session_auth_hash(request, user)
    logger.info(f"User password changed: {user.email}")
    return redirect("/authentication/profile/")
