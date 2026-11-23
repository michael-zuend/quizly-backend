"""JWT authentication that reads the access token from an HttpOnly cookie."""

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate requests with the access token from the cookie."""

    def authenticate(self, request):
        """Return (user, token) or None when no access cookie is sent."""
        # The frontend sends the token as an HttpOnly cookie, not as a header.
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)
        if raw_token is None:
            # No cookie: the request is anonymous, permissions decide (401).
            return None
        # Checks the signature and the expiry date of the token.
        validated_token = self.get_validated_token(raw_token)
        # Loads the user the token belongs to.
        return self.get_user(validated_token), validated_token
