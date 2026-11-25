"""Central URL routing of the Quizly backend."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Django admin panel to manage users, quizzes and questions.
    path("admin/", admin.site.urls),
    # register/, login/, logout/, token/refresh/
    path("api/", include("auth_app.api.urls")),
    # quizzes/ and quizzes/<id>/
    path("api/", include("quiz_app.api.urls")),
]
