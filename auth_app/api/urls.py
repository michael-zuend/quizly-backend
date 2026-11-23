"""URL routes of the auth app."""

from django.urls import path

from .views import LoginView, LogoutView, RegistrationView, TokenRefreshView

urlpatterns = [
    # POST: create a new user account.
    path("register/", RegistrationView.as_view(), name="register"),
    # POST: log in and receive the JWT cookies.
    path("login/", LoginView.as_view(), name="login"),
    # POST: log out, blacklist the refresh token, delete the cookies.
    path("logout/", LogoutView.as_view(), name="logout"),
    # POST: get a new access token cookie from the refresh token cookie.
    path(
        "token/refresh/", TokenRefreshView.as_view(), name="token-refresh"
    ),
]
