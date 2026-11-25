"""Tests for the login endpoint."""

from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle


class LoginTests(APITestCase):
    """POST /api/login/"""

    def setUp(self):
        """Create a user and reset the throttle counters."""
        cache.clear()
        self.url = reverse("login")
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "Str0ngPassw0rd!"
        )
        self.data = {"username": "tester", "password": "Str0ngPassw0rd!"}

    def test_login_returns_user(self):
        """Valid credentials give 200 and the user data."""
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Login successfully!")
        self.assertEqual(response.data["user"], {
            "id": self.user.id,
            "username": "tester",
            "email": "tester@example.com",
        })

    def test_login_sets_httponly_cookies(self):
        """Both tokens are sent as HttpOnly cookies, not in the body."""
        response = self.client.post(self.url, self.data, format="json")
        for name in ("access_token", "refresh_token"):
            self.assertIn(name, response.cookies)
            self.assertTrue(response.cookies[name]["httponly"])
            self.assertEqual(response.cookies[name]["samesite"], "Lax")
        self.assertNotIn("access", response.data)

    def test_wrong_password_gives_generic_error(self):
        """Wrong password and unknown user give the same 401 message."""
        wrong = self.client.post(
            self.url, {"username": "tester", "password": "nope"},
            format="json",
        )
        unknown = self.client.post(
            self.url, {"username": "ghost", "password": "nope"},
            format="json",
        )
        self.assertEqual(wrong.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(wrong.data, unknown.data)

    def test_missing_fields_give_400(self):
        """An empty body is rejected."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_cookie_does_not_block_login(self):
        """An invalid access cookie is ignored on the login."""
        self.client.cookies["access_token"] = "expired-token"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_is_throttled(self):
        """Too many attempts give 429."""
        rates = {"login": "2/minute"}
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", rates):
            for _ in range(2):
                self.client.post(self.url, self.data, format="json")
            response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(
            response.status_code, status.HTTP_429_TOO_MANY_REQUESTS
        )
