"""Tests for the quiz list and GET, PATCH, DELETE of a single quiz."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Question, Quiz

from .helpers import VIDEO_URL, create_quiz, create_user


class QuizListTests(APITestCase):
    """GET /api/quizzes/"""

    def test_list_contains_only_own_quizzes(self):
        """Quizzes of other users are not listed."""
        user = create_user()
        own_quiz = create_quiz(user)
        create_quiz(create_user("other"))
        self.client.force_authenticate(user)
        response = self.client.get(reverse("quiz-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([quiz["id"] for quiz in response.data], [own_quiz.id])
        self.assertEqual(response.data[0]["video_url"], VIDEO_URL)

    def test_list_requires_login(self):
        """Anonymous users get 401."""
        response = self.client.get(reverse("quiz-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class QuizDetailTests(APITestCase):
    """GET, PATCH and DELETE /api/quizzes/{id}/"""

    def setUp(self):
        """Create a quiz and log in as its owner."""
        self.owner = create_user()
        self.quiz = create_quiz(self.owner)
        self.url = reverse("quiz-detail", args=[self.quiz.id])
        self.client.force_authenticate(self.owner)

    def test_get_returns_quiz(self):
        """The owner gets the quiz with all fields."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {
            "id", "title", "description", "created_at", "updated_at",
            "video_url", "questions",
        })

    def test_patch_updates_title_and_description(self):
        """Only title and description can be changed."""
        response = self.client.patch(self.url, {
            "title": "New title",
            "description": "New text",
            "video_url": "https://evil.com",
        }, format="json")
        self.quiz.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.quiz.title, "New title")
        self.assertEqual(self.quiz.description, "New text")
        self.assertEqual(self.quiz.video_url, VIDEO_URL)

    def test_patch_with_empty_title_gives_400(self):
        """The title cannot be empty."""
        response = self.client.patch(self.url, {"title": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_is_not_allowed(self):
        """PUT is not part of the API."""
        response = self.client.put(self.url, {"title": "x"}, format="json")
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_delete_removes_quiz_and_questions(self):
        """DELETE gives 204 and removes the questions too."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.exists())
        self.assertFalse(Question.objects.exists())

    def test_foreign_quiz_gives_403(self):
        """Other users can neither read, change nor delete the quiz."""
        self.client.force_authenticate(create_user("other"))
        for method in ("get", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(
                    response.status_code, status.HTTP_403_FORBIDDEN
                )

    def test_missing_quiz_gives_404(self):
        """An unknown id gives 404."""
        url = reverse("quiz-detail", args=[self.quiz.id + 100])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_requires_login(self):
        """Anonymous users get 401."""
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
