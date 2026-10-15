from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


class SuperuserOnlyMiddleware:
    EXEMPT_PATHS = {
        "/login/",
        "/logout/",
        "/role-redirect/",
        "/password-reset/",
        "/password-reset/sent/",
        "/reset/complete/",
    }

    # Staff users are allowed to access only these paths at the middleware level.
    # Individual views must still enforce their own permissions.
    STAFF_ALLOWED_PATHS = (
        "/tenants/add/",
        "/owners/add/",
        "/property/add/",
        "/agreements/add/",
        "/property-tax/",
        "/tenants/",
        "/owners/",
        "/property/",
        "/agreements/",
        "/profile/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Allow authentication and password-reset pages.
        if path in self.EXEMPT_PATHS or path.startswith("/reset/"):
            return self.get_response(request)

        # Allow static and media files.
        if settings.STATIC_URL and path.startswith(settings.STATIC_URL):
            return self.get_response(request)

        if settings.MEDIA_URL and path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        user = request.user

        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        if not user.is_active:
            return HttpResponseForbidden("This account is inactive.")

        # Administrators can pass through this middleware.
        if user.is_superuser:
            return self.get_response(request)

       # Allow Staff to open the dashboard.
        # Allow Staff to open the dashboard.
        if request.path == "/":
            return self.get_response(request)

        # Allow Staff URLs listed in the allowlist.
        if request.path in self.STAFF_ALLOWED_PATHS or any(
            request.path.startswith(prefix)
            for prefix in self.STAFF_ALLOWED_PATHS
        ):
            return self.get_response(request)

        return HttpResponseForbidden(
            "Access denied. This page is restricted to Administrators."
        )