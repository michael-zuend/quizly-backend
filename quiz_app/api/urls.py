"""URL routes of the quiz app."""

from django.urls import path

from .views import QuizDetailView, QuizListCreateView

urlpatterns = [
    # GET: list own quizzes, POST: create a quiz from a YouTube URL.
    path("quizzes/", QuizListCreateView.as_view(), name="quiz-list"),
    # GET, PATCH, DELETE of one quiz.
    path("quizzes/<int:pk>/", QuizDetailView.as_view(), name="quiz-detail"),
]
