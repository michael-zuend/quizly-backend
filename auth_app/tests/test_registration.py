"""Tests for the registration endpoint."""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class RegistrationTests(APITestCase):
    """POST /api/register/"""

    def setUp(self):
        """Reset the throttle counters and prepare valid data."""
        cache.clear()
        self.url = reverse("register")
        self.data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Str0ngPassw0rd!",
            "confirmed_password": "Str0ngPassw0rd!",
        }

    def test_register_creates_user(self):
        """Valid data creates a user with a hashed password."""
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data, {"detail": "User created successfully!"}
        )
        user = User.objects.get(username="newuser")
        self.assertTrue(user.check_password("Str0ngPassw0rd!"))
        self.assertNotEqual(user.password, "Str0ngPassw0rd!")

    def test_passwords_must_match(self):
        """Different passwords give 400."""
        self.data["confirmed_password"] = "Other0ne!xyz"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirmed_password", response.data)

    def test_email_must_be_unique(self):
        """An email that is already used (any case) gives 400."""
        User.objects.create_user("old", "NewUser@Example.com", "x")
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_email_is_required(self):
        """A missing email gives 400."""
        del self.data["email"]
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_is_rejected(self):
        """The Django password validators are applied."""
        self.data["password"] = self.data["confirmed_password"] = "123"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_password_is_not_returned(self):
        """The response never contains the password."""
        response = self.client.post(self.url, self.data, format="json")
        self.assertNotIn("password", response.data)

    def test_invalid_cookie_does_not_block_registration(self):
        """An old access cookie is ignored on this public endpoint."""
        self.client.cookies["access_token"] = "broken-token"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
