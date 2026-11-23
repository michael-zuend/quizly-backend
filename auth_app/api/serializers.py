"""Serializers for registration and login."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate registration data and create a new user."""

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirmed_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        """Reject an email address that is already in use."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate(self, attrs):
        """Make sure both passwords match."""
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """Create the user with a hashed password."""
        validated_data.pop("confirmed_password")
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Check username and password and return the user."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate the user with a generic error message."""
        user = authenticate(
            username=attrs["username"], password=attrs["password"]
        )
        if user is None:
            raise AuthenticationFailed("Invalid username or password.")
        attrs["user"] = user
        return attrs