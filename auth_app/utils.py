"""Helper functions for the auth cookies."""

from django.conf import settings


def set_auth_cookie(response, name, value, lifetime):
    """Set one JWT as a secure HttpOnly cookie."""
    response.set_cookie(
        name,
        value,
        max_age=int(lifetime.total_seconds()),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def set_login_cookies(response, refresh):
    """Set the access and refresh token cookies after login."""
    jwt_settings = settings.SIMPLE_JWT
    set_auth_cookie(
        response, settings.AUTH_COOKIE_ACCESS,
        str(refresh.access_token), jwt_settings["ACCESS_TOKEN_LIFETIME"],
    )
    set_auth_cookie(
        response, settings.AUTH_COOKIE_REFRESH,
        str(refresh), jwt_settings["REFRESH_TOKEN_LIFETIME"],
    )