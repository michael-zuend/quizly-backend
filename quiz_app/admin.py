"""Admin configuration for quizzes and questions."""

from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.StackedInline):
    """Edit the questions directly on the quiz page."""

    # Model shown inside the quiz form.
    model = Question
    # No empty extra forms, Gemini always creates ten questions.
    extra = 0
    # Fields that can be edited.
    fields = ["question_title", "question_options", "answer"]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin page for quizzes including their questions."""

    # Columns of the quiz list.
    list_display = ["id", "title", "owner", "created_at", "updated_at"]
    # Clickable columns that open the edit page.
    list_display_links = ["id", "title"]
    # Search by title, description and username of the owner.
    search_fields = ["title", "description", "owner__username"]
    # Filter in the right sidebar.
    list_filter = ["created_at"]
    # Timestamps are set automatically and cannot be edited.
    readonly_fields = ["created_at", "updated_at"]
    # Questions are edited on the same page.
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin page to edit single questions."""

    # Columns of the question list.
    list_display = ["id", "question_title", "quiz", "answer"]
    # Search by question text and quiz title.
    search_fields = ["question_title", "quiz__title"]
    # Filter questions by quiz.
    list_filter = ["quiz"]
    # Timestamps are set automatically and cannot be edited.
    readonly_fields = ["created_at", "updated_at"]
