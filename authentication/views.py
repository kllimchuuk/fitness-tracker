import logging
import re

from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect

from .models import User

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PASSWORD_MIN_LEN = 8
AGE_MIN, AGE_MAX = 1, 120
HEIGHT_MIN, HEIGHT_MAX = 50.0, 300.0
GOAL_MAX_LEN = 256
logger = logging.getLogger(__name__)


def validate_email(email: str) -> str | None:
    if not email:
        return "Email is required"
    if not EMAIL_REGEX.match(email):
        return "Invalid email format"
    if User.objects.filter(email=email).exists():
        return "Email already exists"
    return None


def validate_password(password: str) -> str | None:
    if len(password) < PASSWORD_MIN_LEN:
        return f"Password must be at least {PASSWORD_MIN_LEN} characters"
    return None


def validate_age(age: str) -> tuple[int | None, str | None]:
    if not age:
        return None, None

    try:
        age_int = int(age)
        if age_int < AGE_MIN or age_int > AGE_MAX:
            return None, "Invalid age"
        return age_int, None
    except ValueError:
        return None, "Invalid age"


def validate_height(height: str) -> tuple[float | None, str | None]:
    if not height:
        return None, None

    try:
        height_float = float(height)
        if height_float < HEIGHT_MIN or height_float > HEIGHT_MAX:
            return None, "Invalid height"
        return height_float, None
    except ValueError:
        return None, "Invalid height"


def validate_goal(goal: str) -> tuple[str | None, str | None]:
    if not goal:
        return None, None
    if len(goal) > GOAL_MAX_LEN:
        return None, f"Goal must be {GOAL_MAX_LEN} characters or less"
    return goal, None


def create_user(
    email: str, password: str, age: int | None, height: float | None, goal: str | None
) -> User:
    user = User(email=email)
    user.password = make_password(password)
    user.status = User.Status.CUSTOMER

    if age:
        user.age = age
    if height:
        user.height = height
    if goal:
        user.goal = goal

    return user


def create_and_save_user(
    email: str, password: str, age: int | None, height: float | None, goal: str | None
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

    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    age = request.POST.get("age", "")
    height = request.POST.get("height", "")
    goal = request.POST.get("goal", "").strip()

    email_error = validate_email(email)
    if email_error:
        return render_error(request, email_error)

    password_error = validate_password(password)
    if password_error:
        return render_error(request, password_error)

    validated_age, age_error = validate_age(age)
    if age_error:
        return render_error(request, age_error)

    validated_height, height_error = validate_height(height)
    if height_error:
        return render_error(request, height_error)

    validated_goal, goal_error = validate_goal(goal)
    if goal_error:
        return render_error(request, goal_error)

    try:
        user = create_and_save_user(
            email, password, validated_age, validated_height, validated_goal
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return render_error(request, "Registration failed. Please try again.")

    request.session.cycle_key()
    request.session["user_id"] = user.id
    request.session["email"] = email
    logger.info(f"New user registered: {email}")
    return redirect("/")


@csrf_protect
def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not email or not password:
            return render(request, "login.html", {"error": "Invalid credentials"})

        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password):
                request.session.cycle_key()
                request.session["user_id"] = user.id
                request.session["email"] = email

                logger.info(f"User logged in: {email}")
                return redirect("/")
            else:
                logger.warning(f"Failed login attempt for email: {email}")
                return render(request, "login.html", {"error": "Invalid credentials"})
        except User.DoesNotExist:
            logger.warning(f"Login attempt for non-existent email: {email}")
            return render(request, "login.html", {"error": "Invalid credentials"})

    return render(request, "login.html")


@csrf_protect
def logout_view(request: HttpRequest) -> HttpResponse:
    email = request.session.get("email", "Unknown")
    request.session.flush()
    logger.info(f"User logged out: {email}")
    return redirect("/authentication/login/")
