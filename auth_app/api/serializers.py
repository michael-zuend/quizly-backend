"""Serializers for registration and login."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate registration data and create a new user."""

    # Second password field, only used for the comparison.
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        # Uses the built-in Django user model.
        model = User
        # Fields the frontend sends on registration.
        fields = ["username", "email", "password", "confirmed_password"]
        # The password is never sent back in a response.
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True, "allow_blank": False},
        }

    def validate_email(self, value):
        """Reject an email address that is already in use."""
        # Case insensitive, so Test@x.ch and test@x.ch count as the same.
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate(self, attrs):
        """Make sure both passwords match and the password is strong."""
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match."}
            )
        # Unsaved user, so the similarity validator can compare the
        # password with username and email.
        user = User(username=attrs["username"], email=attrs["email"])
        # Runs the AUTH_PASSWORD_VALIDATORS from the settings.
        validate_password(attrs["password"], user)
        return attrs

    def create(self, validated_data):
        """Create the user with a hashed password."""
        # The confirmation is not a field of the user model.
        validated_data.pop("confirmed_password")
        # create_user hashes the password (never stored in plain text).
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Check username and password and return the user."""

    # Username of the account.
    username = serializers.CharField()
    # Password, never part of a response.
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate the user with a generic error message."""
        # Django checks the password hash, returns None on failure.
        user = authenticate(
            username=attrs["username"], password=attrs["password"]
        )
        if user is None:
            # Same message for unknown user and wrong password, so an
            # attacker cannot find out which usernames exist.
            raise AuthenticationFailed("Invalid username or password.")
        # The view reads the user from validated_data.
        attrs["user"] = user
        return attrs
