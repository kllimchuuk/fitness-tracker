from functools import wraps
from typing import Any, Callable

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from .models import User


def require_auth(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("/authentication/login/")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            request.session.flush()
            return redirect("/authentication/login/")

        setattr(request, "current_user", user)
        return view_func(request, *args, **kwargs)

    return wrapper
