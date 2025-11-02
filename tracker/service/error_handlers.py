import logging

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def handle_service_error(e: Exception, user_message: str = "Something went wrong.", status: int = 400):
    logger.warning(f"Service error: {e}")
    return JsonResponse({"detail": user_message}, status=status)


def handle_unexpected_error(e: Exception, context: str = ""):
    logger.exception(f"Unexpected error in {context}: {e}")
    return JsonResponse({"detail": "Internal server error."}, status=500)
