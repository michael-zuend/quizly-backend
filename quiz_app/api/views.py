"""Views for creating, listing, updating and deleting quizzes."""

import logging

from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from quiz_app.models import Quiz
from quiz_app.utils import (
    QuizGenerationError,
    VideoDownloadError,
    create_quiz_from_url,
)

from .permissions import IsQuizOwner
from .serializers import QuizCreateSerializer, QuizSerializer

# Errors are written to the server log, the client gets a short message.
logger = logging.getLogger(__name__)
# Generic message for the client when the AI pipeline fails.
GENERATION_ERROR = "Quiz could not be created."


class QuizListCreateView(ListAPIView):
    """GET: list the quizzes of the user. POST: create a new quiz."""

    # Output format of the quizzes.
    serializer_class = QuizSerializer
    # Rate of this scope is defined in settings.REST_FRAMEWORK.
    throttle_scope = "quiz_create"

    def get_throttles(self):
        """Throttle only POST, creating a quiz is expensive."""
        # GET (list) stays unlimited.
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return []

    def get_queryset(self):
        """Return only the quizzes of the logged in user."""
        # prefetch_related loads all questions with one extra query.
        return Quiz.objects.filter(owner=self.request.user).prefetch_related(
            "questions"
        )

    def post(self, request):
        """Create a quiz from a YouTube URL (download, Whisper, Gemini)."""
        # Invalid or non YouTube URL ends here with 400.
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data["url"]
        try:
            quiz = create_quiz_from_url(request.user, url)
        except VideoDownloadError as error:
            # Private, deleted, too long or live video: client error.
            return Response({"detail": str(error)}, status=400)
        except QuizGenerationError as error:
            # Details only in the log, never internals to the client.
            logger.warning("Quiz generation failed: %s", error)
            return Response({"detail": GENERATION_ERROR}, status=500)
        return Response(QuizSerializer(quiz).data, status=201)


class QuizDetailView(RetrieveUpdateDestroyAPIView):
    """GET, PATCH and DELETE of a single quiz (owner only)."""

    # All quizzes: a foreign quiz gives 403, a missing quiz 404.
    queryset = Quiz.objects.prefetch_related("questions")
    serializer_class = QuizSerializer
    # Logged in (401) and owner of the quiz (403).
    permission_classes = [IsAuthenticated, IsQuizOwner]
    # PUT is not part of the API, only partial updates are allowed.
    http_method_names = ["get", "patch", "delete", "head", "options"]
