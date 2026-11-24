"""Serializers for quizzes and questions."""

from rest_framework import serializers

from quiz_app.models import Question, Quiz
from quiz_app.utils import InvalidVideoUrlError, extract_video_id


class QuestionSerializer(serializers.ModelSerializer):
    """Read-only representation of one question."""

    class Meta:
        model = Question
        # Field names as defined in the API documentation.
        fields = [
            "id",
            "question_title",
            "question_options",
            "answer",
            "created_at",
            "updated_at",
        ]
        # Questions are created by the AI and edited only in the admin.
        read_only_fields = fields


class QuizSerializer(serializers.ModelSerializer):
    """Quiz with all questions. Only title and description are writable."""

    # All questions of the quiz, nested in the response.
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        # Field names as defined in the API documentation.
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]
        # PATCH may only change title and description.
        read_only_fields = ["id", "created_at", "updated_at", "video_url"]
        # The description may be empty, the title not.
        extra_kwargs = {"description": {"allow_blank": True}}


class QuizCreateSerializer(serializers.Serializer):
    """Validate the YouTube URL sent to create a quiz."""

    # The frontend sends {"url": "..."}.
    url = serializers.URLField(max_length=500)

    def validate_url(self, value):
        """Accept only real YouTube video URLs (400 otherwise)."""
        try:
            extract_video_id(value)
        except InvalidVideoUrlError as error:
            raise serializers.ValidationError(str(error))
        return value
