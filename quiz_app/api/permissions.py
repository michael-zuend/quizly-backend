"""Permissions for quizzes."""

from rest_framework.permissions import BasePermission


class IsQuizOwner(BasePermission):
    """Allow access to a quiz only for the user who created it."""

    # Message of the 403 response.
    message = "You do not have permission to access this quiz."

    def has_object_permission(self, request, view, obj):
        """Compare the owner of the quiz with the logged in user."""
        return obj.owner_id == request.user.id
