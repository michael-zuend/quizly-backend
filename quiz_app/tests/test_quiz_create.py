"""Tests for POST /api/quizzes/"""

from unittest import mock

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle

from quiz_app.utils import QuizGenerationError, VideoDownloadError

from .helpers import create_quiz, create_user

PIPELINE = "quiz_app.api.views.create_quiz_from_url"
YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


class QuizCreateTests(APITestCase):
    """Creating a quiz from a YouTube URL."""

    def setUp(self):
        """Reset the throttle counters and log in a user."""
        cache.clear()
        self.user = create_user()
        self.client.force_authenticate(self.user)
        self.url = reverse("quiz-list")

    def post_url(self, url=YOUTUBE_URL):
        """Helper: send a URL to the create endpoint."""
        return self.client.post(self.url, {"url": url}, format="json")

    @mock.patch(PIPELINE)
    def test_create_returns_quiz(self, pipeline):
        """201 with the quiz and its ten questions."""
        pipeline.side_effect = lambda owner, url: create_quiz(owner)
        response = self.post_url()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["questions"]), 10)
        self.assertEqual(set(response.data["questions"][0]), {
            "id", "question_title", "question_options", "answer",
            "created_at", "updated_at",
        })
        pipeline.assert_called_once_with(self.user, YOUTUBE_URL)

    def test_non_youtube_url_gives_400(self):
        """Other websites are rejected before any download."""
        response = self.post_url("https://example.com/video")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_url_gives_400(self):
        """An empty body is rejected."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch(PIPELINE, side_effect=VideoDownloadError("not available"))
    def test_download_error_gives_400(self, pipeline):
        """A private or too long video is a client error."""
        response = self.post_url()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "not available")

    @mock.patch(PIPELINE, side_effect=QuizGenerationError("secret detail"))
    def test_generation_error_gives_500(self, pipeline):
        """AI errors give 500 without internal details."""
        with self.assertLogs("quiz_app.api.views", level="WARNING"):
            response = self.post_url()
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertNotIn("secret", response.data["detail"])

    def test_create_requires_login(self):
        """Anonymous users get 401."""
        self.client.force_authenticate(None)
        response = self.post_url()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch(PIPELINE)
    def test_create_is_throttled(self, pipeline):
        """Too many quiz creations give 429, the list stays open."""
        pipeline.side_effect = lambda owner, url: create_quiz(owner)
        rates = {"quiz_create": "1/hour"}
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", rates):
            self.post_url()
            response = self.post_url()
            list_response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_429_TOO_MANY_REQUESTS
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
