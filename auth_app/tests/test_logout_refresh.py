"""Tests for logout, token refresh and the cookie authentication."""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


class LogoutAndRefreshTests(APITestCase):
    """POST /api/logout/ and POST /api/token/refresh/"""

    def setUp(self):
        """Create a user and log in, the client keeps the cookies."""
        cache.clear()
        User.objects.create_user("tester", "t@example.com", "Str0ngPassw0rd!")
        self.client.post(
            reverse("login"),
            {"username": "tester", "password": "Str0ngPassw0rd!"},
            format="json",
        )

    def test_refresh_sets_new_access_cookie(self):
        """A valid refresh cookie gives a new access cookie."""
        response = self.client.post(reverse("token-refresh"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Token refreshed"})
        self.assertTrue(response.cookies["access_token"]["httponly"])

    def test_refresh_without_cookie_gives_401(self):
        """No refresh cookie gives 401."""
        self.client.cookies.clear()
        response = self.client.post(reverse("token-refresh"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_invalid_cookie_gives_401(self):
        """A manipulated refresh token gives 401."""
        self.client.cookies["refresh_token"] = "manipulated"
        response = self.client.post(reverse("token-refresh"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_and_deletes_cookies(self):
        """Logout puts the refresh token on the blacklist."""
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Log-Out successfully!", response.data["detail"])
        self.assertEqual(BlacklistedToken.objects.count(), 1)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_refresh_after_logout_gives_401(self):
        """The old refresh token cannot be used after logout."""
        refresh_token = self.client.cookies["refresh_token"].value
        self.client.post(reverse("logout"))
        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post(reverse("token-refresh"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_login_gives_401(self):
        """Logout requires a valid access cookie."""
        self.client.cookies.clear()
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_refresh_cookie(self):
        """An invalid refresh token does not break the logout."""
        self.client.cookies["refresh_token"] = "broken"
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_access_cookie_gives_401(self):
        """A manipulated access cookie is rejected on protected routes."""
        self.client.cookies["access_token"] = "manipulated"
        response = self.client.get(reverse("quiz-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
