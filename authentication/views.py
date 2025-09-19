import logging
import re

from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError

from .models import User

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PASSWORD_MIN_LEN = 8
AGE_MIN, AGE_MAX = 1, 120
HEIGHT_MIN, HEIGHT_MAX = 50.0, 300.0
GOAL_MAX_LEN = 256
logger = logging.getLogger(__name__)


def validate_email(email: str, check_exists: bool = True) -> str:
    email = (email or "").strip()
    if not email:
        raise ValidationError("Email is required")
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Invalid email format")
    if check_exists and User.objects.filter(email=email).exists():
        raise ValidationError("Email already exists")
    return email


def validate_password(password: str) -> str:
    if len(password) < PASSWORD_MIN_LEN:
        raise ValidationError(
            f"Password must be at least {PASSWORD_MIN_LEN} characters"
        )
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


def create_user(email: str, password: str, age: int, height: float, goal: str) -> User:
    user = User(email=email)
    user.password = make_password(password)
    user.status = User.Status.CUSTOMER

    user.age = age
    user.height = height
    user.goal = goal

    return user


def create_and_save_user(
    email: str, password: str, age: int, height: float, goal: str
) -> User:
    user = create_user(email, password, age, height, goal)
    user.save()
    return user


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
        user = create_and_save_user(
            validated_email, validated_password, age_int, height_float, goal_str
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return render_error(request, "Registration failed. Please try again.")

    request.session.cycle_key()
    request.session["user_id"] = user.id
    request.session["email"] = validated_email
    logger.info(f"New user registered: {validated_email}")
    return redirect("/")

def authenticate_user(email: str, password: str) -> User:
    user = User.objects.get(email=email)
    if not check_password(password, user.password):
        raise ValidationError("Invalid password")
    return user

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

        try:
            user = authenticate_user(validated_email, password)
        except (ValidationError, User.DoesNotExist):
            logger.warning(f"Login attempt for non-existent email: {validated_email}")
            return render(request, "login.html", {"error": "Invalid credentials"})

        request.session.cycle_key()
        request.session["user_id"] = user.id
        request.session["email"] = validated_email
        logger.info(f"User logged in: {validated_email}")
        return redirect("/")

    return render(request, "login.html")


@csrf_protect
def logout_view(request: HttpRequest) -> HttpResponse:
    email = request.session.get("email", "Unknown")

    if email != "Unknown":
        try:
            validated_email = validate_email(email, check_exists=False)
        except ValidationError:
            validated_email = "Invalid email format"
    else:
        validated_email = "Unknown"

    request.session.flush()
    logger.info(f"User logged out: {validated_email}")
    return redirect("/authentication/login/")
