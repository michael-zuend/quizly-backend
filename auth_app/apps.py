"""App configuration of the auth app."""

from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """Registration, login, logout and token refresh with JWT cookies."""

    name = "auth_app"
