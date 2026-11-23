"""Helper functions for the auth cookies."""

from django.conf import settings
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken


def set_auth_cookie(response, name, value, lifetime):
    """Set one JWT as a secure HttpOnly cookie."""
    response.set_cookie(
        # Cookie name, for example "access_token".
        name,
        # The encoded JWT.
        value,
        # The cookie expires together with the token.
        max_age=int(lifetime.total_seconds()),
        # JavaScript cannot read the cookie (protection against XSS).
        httponly=True,
        # Only sent over HTTPS in production (DEBUG=False).
        secure=settings.AUTH_COOKIE_SECURE,
        # Not sent with cross-site POST requests (protection against CSRF).
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def set_access_cookie(response, access_token):
    """Set only the access token cookie (used by the token refresh)."""
    # Lifetime comes from the SIMPLE_JWT settings (15 minutes).
    lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
    # Writes the new access token into the cookie.
    set_auth_cookie(
        response, settings.AUTH_COOKIE_ACCESS, str(access_token), lifetime
    )


def set_login_cookies(response, refresh):
    """Set the access and refresh token cookies after login."""
    # The access token is derived from the refresh token.
    set_access_cookie(response, refresh.access_token)
    # Lifetime of the refresh token (1 day).
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    # Writes the refresh token into its own cookie.
    set_auth_cookie(
        response, settings.AUTH_COOKIE_REFRESH, str(refresh), lifetime
    )


def delete_login_cookies(response):
    """Remove both JWT cookies from the browser."""
    # Same SameSite value as on login, so the browser matches the cookie.
    samesite = settings.AUTH_COOKIE_SAMESITE
    # Deletes the access token cookie.
    response.delete_cookie(settings.AUTH_COOKIE_ACCESS, samesite=samesite)
    # Deletes the refresh token cookie.
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH, samesite=samesite)


def get_user_data(user):
    """Return the public user data for the login response."""
    # Only id, username and email, never the password hash.
    return {"id": user.id, "username": user.username, "email": user.email}


def blacklist_refresh_token(raw_token):
    """Put a refresh token on the blacklist, ignore invalid tokens."""
    try:
        # A blacklisted token can never be used again.
        RefreshToken(raw_token).blacklist()
    except TokenError:
        # Missing or already invalid token: nothing left to blacklist.
        pass


def create_access_token(raw_token):
    """Validate the refresh token and return a new access token."""
    if raw_token is None:
        # No cookie means not logged in: 401 instead of 400.
        raise InvalidToken("Refresh token cookie is missing.")
    # Checks signature, expiry date and the blacklist.
    serializer = TokenRefreshSerializer(data={"refresh": raw_token})
    try:
        serializer.is_valid(raise_exception=True)
    except TokenError as error:
        # Invalid or blacklisted token: 401 for the frontend.
        raise InvalidToken(error.args[0])
    return serializer.validated_data["access"]
