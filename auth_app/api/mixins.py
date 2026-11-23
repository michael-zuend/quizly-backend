"""Shared view behaviour for the public auth endpoints."""


class PublicAuthViewMixin:
    """Ignore auth cookies but still answer failed logins with 401."""

    # Old or expired cookies must not block login, register or refresh.
    authentication_classes = []

    def get_authenticate_header(self, request):
        """Return a WWW-Authenticate value, so DRF sends 401 not 403."""
        # Without this header DRF turns AuthenticationFailed into 403.
        return 'Bearer realm="api"'
