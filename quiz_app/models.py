"""Models for quizzes and their questions."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

# Every question has exactly this number of answer options.
OPTIONS_PER_QUESTION = 4


class Quiz(models.Model):
    """A quiz generated from one YouTube video."""

    # User who created the quiz. Deleting the user deletes his quizzes.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    # Title written by Gemini, the user can change it later.
    title = models.CharField(max_length=255)
    # Short description written by Gemini, editable by the user.
    description = models.TextField(blank=True)
    # Normalized YouTube URL, the frontend embeds the video with it.
    video_url = models.URLField(max_length=255)
    # Set once when the quiz is created.
    created_at = models.DateTimeField(auto_now_add=True)
    # Updated on every save.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Newest quizzes first.
        ordering = ["-created_at"]
        verbose_name_plural = "quizzes"

    def __str__(self):
        """Show the title in the admin panel."""
        return self.title


class Question(models.Model):
    """One multiple choice question of a quiz."""

    # Quiz the question belongs to, quiz.questions returns all of them.
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions"
    )
    # The question text.
    question_title = models.CharField(max_length=500)
    # List with exactly four answer options (stored as JSON).
    question_options = models.JSONField(default=list)
    # The correct option, it is always one of question_options.
    answer = models.CharField(max_length=255)
    # Set once when the question is created.
    created_at = models.DateTimeField(auto_now_add=True)
    # Updated on every save.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Questions keep the order in which Gemini created them.
        ordering = ["id"]

    def __str__(self):
        """Show the question text in the admin panel."""
        return self.question_title

    def clean(self):
        """Check the options and the answer (used by the admin form)."""
        options = self.question_options
        # Exactly four options are required.
        if not isinstance(options, list) or len(options) != (
            OPTIONS_PER_QUESTION
        ):
            raise ValidationError(
                {"question_options": "Exactly four options are required."}
            )
        # The correct answer must be one of the options.
        if self.answer not in options:
            raise ValidationError(
                {"answer": "The answer must be one of the options."}
            )
