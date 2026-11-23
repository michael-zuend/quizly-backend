"""Views for register, login, logout and token refresh."""

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.utils import (
    blacklist_refresh_token,
    create_access_token,
    delete_login_cookies,
    get_user_data,
    set_access_cookie,
    set_login_cookies,
)

from .mixins import PublicAuthViewMixin
from .serializers import LoginSerializer, RegistrationSerializer

# Logout message as defined in the API documentation.
LOGOUT_MESSAGE = (
    "Log-Out successfully! All Tokens will be deleted. "
    "Refresh token is now invalid."
)


class RegistrationView(PublicAuthViewMixin, APIView):
    """Register a new user."""

    # Everybody may register, no login required.
    permission_classes = [AllowAny]
    # Limits the number of registrations per IP (brute force / spam).
    throttle_classes = [ScopedRateThrottle]
    # Rate of this scope is defined in settings.REST_FRAMEWORK.
    throttle_scope = "register"

    def post(self, request):
        """Validate the data and create the user."""
        # Fill the serializer with the JSON body of the request.
        serializer = RegistrationSerializer(data=request.data)
        # Invalid data ends here with a 400 response.
        serializer.is_valid(raise_exception=True)
        # Creates the user with a hashed password.
        serializer.save()
        # 201 with the message defined in the API documentation.
        return Response(
            {"detail": "User created successfully!"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(PublicAuthViewMixin, APIView):
    """Log in a user and set the JWT cookies."""

    # Everybody may try to log in.
    permission_classes = [AllowAny]
    # Limits login attempts per IP (password brute force).
    throttle_classes = [ScopedRateThrottle]
    # Rate of this scope is defined in settings.REST_FRAMEWORK.
    throttle_scope = "login"

    def post(self, request):
        """Check the credentials and send the tokens as cookies."""
        # Validates username and password (generic error on failure).
        serializer = LoginSerializer(data=request.data)
        # Wrong credentials end here with a 401 response.
        serializer.is_valid(raise_exception=True)
        # The serializer stored the authenticated user.
        user = serializer.validated_data["user"]
        # Response body as defined in the API documentation.
        response = Response({
            "detail": "Login successfully!", "user": get_user_data(user),
        })
        # Creates access + refresh token and sets them as HttpOnly cookies.
        set_login_cookies(response, RefreshToken.for_user(user))
        return response


class LogoutView(APIView):
    """Log out the user, blacklist the refresh token, delete the cookies."""

    # Only a logged in user can log out (401 otherwise).
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Invalidate the refresh token and remove both cookies."""
        # The refresh token is stored in its own HttpOnly cookie.
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        # Puts the token on the blacklist, it cannot be used again.
        blacklist_refresh_token(raw_token)
        # Message as defined in the API documentation.
        response = Response({"detail": LOGOUT_MESSAGE})
        # The browser deletes both cookies.
        delete_login_cookies(response)
        return response


class TokenRefreshView(PublicAuthViewMixin, APIView):
    """Create a new access token from the refresh token cookie."""

    # The refresh token in the cookie is the proof of the login.
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate the refresh cookie and set a new access cookie."""
        # Reads the refresh token from its HttpOnly cookie.
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        # Invalid, missing or blacklisted token ends here with 401.
        access_token = create_access_token(raw_token)
        # Message as defined in the API documentation.
        response = Response({"detail": "Token refreshed"})
        # Sends the new access token as HttpOnly cookie.
        set_access_cookie(response, access_token)
        return response
