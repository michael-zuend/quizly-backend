"""Tests for the quiz models and the admin panel."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from quiz_app.models import Question

from .helpers import create_quiz, create_user


class ModelTests(TestCase):
    """Quiz and Question models."""

    def setUp(self):
        """Create a quiz with ten questions."""
        self.quiz = create_quiz(create_user())

    def test_string_representations(self):
        """__str__ returns title and question text."""
        question = self.quiz.questions.first()
        self.assertEqual(str(self.quiz), "Test Quiz")
        self.assertEqual(str(question), "Question 0?")

    def test_questions_are_saved(self):
        """All ten questions belong to the quiz."""
        self.assertEqual(self.quiz.questions.count(), 10)

    def test_clean_accepts_valid_question(self):
        """A valid question passes the model validation."""
        self.quiz.questions.first().clean()

    def test_clean_rejects_wrong_option_count(self):
        """Three options are not allowed."""
        question = Question(question_options=["a", "b", "c"], answer="a")
        with self.assertRaises(ValidationError):
            question.clean()

    def test_clean_rejects_unknown_answer(self):
        """The answer must be one of the options."""
        question = Question(question_options=list("abcd"), answer="x")
        with self.assertRaises(ValidationError):
            question.clean()


class AdminTests(TestCase):
    """The admin panel lists and edits quizzes and questions."""

    def setUp(self):
        """Log in as superuser and create a quiz."""
        admin_user = create_user("admin")
        admin_user.is_staff = admin_user.is_superuser = True
        admin_user.save()
        self.client.force_login(admin_user)
        self.quiz = create_quiz(admin_user)

    def test_quiz_pages_load(self):
        """Quiz list and quiz edit page (with questions) work."""
        list_page = self.client.get(reverse("admin:quiz_app_quiz_changelist"))
        edit_page = self.client.get(
            reverse("admin:quiz_app_quiz_change", args=[self.quiz.id])
        )
        self.assertEqual(list_page.status_code, 200)
        self.assertContains(edit_page, "Question 0?")

    def test_question_pages_load(self):
        """Question list and question edit page work."""
        question = self.quiz.questions.first()
        list_page = self.client.get(
            reverse("admin:quiz_app_question_changelist")
        )
        edit_page = self.client.get(
            reverse("admin:quiz_app_question_change", args=[question.id])
        )
        self.assertEqual(list_page.status_code, 200)
        self.assertEqual(edit_page.status_code, 200)
