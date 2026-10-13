
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden


class SuperuserOnlyMiddleware:
    EXEMPT_PATHS = {
    "/login/",
    "/logout/",
    "/password-reset/",
    "/password-reset/sent/",
    "/reset/complete/",
 }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/reset/"):
            return self.get_response(request)
        # Allow login and logout endpoints.
        if request.path in self.EXEMPT_PATHS:
            return self.get_response(request)

        # Allow static and media files.
        if settings.STATIC_URL and request.path.startswith(settings.STATIC_URL):
            return self.get_response(request)

        if settings.MEDIA_URL and request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        user = request.user

        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        if not user.is_active or not user.is_superuser:
            return HttpResponseForbidden(
                "Access denied. An active superuser account is required."
            )

        return self.get_response(request)
