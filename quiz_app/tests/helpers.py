"""Shared test data for the quiz tests."""

from django.contrib.auth.models import User

from quiz_app.utils import save_quiz

# Normalized URL of a test video.
VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def make_question(number):
    """Return one valid question as Gemini would send it."""
    options = [f"Option {number}{letter}" for letter in "ABCD"]
    return {
        "question_title": f"Question {number}?",
        "question_options": options,
        "answer": options[0],
    }


def make_quiz_data():
    """Return a complete, valid Gemini answer with ten questions."""
    return {
        "title": "Test Quiz",
        "description": "A quiz about a test video.",
        "questions": [make_question(number) for number in range(10)],
    }


def create_user(username="tester"):
    """Create a user with a fixed password."""
    return User.objects.create_user(
        username, f"{username}@example.com", "Str0ngPassw0rd!"
    )


def create_quiz(owner):
    """Create a saved quiz with ten questions for the owner."""
    return save_quiz(owner, VIDEO_URL, make_quiz_data())
