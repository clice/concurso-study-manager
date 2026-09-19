from django.contrib import admin

from .models import QuestionRecord


@admin.register(QuestionRecord)
class QuestionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "answered_date",
        "question_number",
        "competition_discipline",
        "board",
        "result",
        "review_required",
    )
    list_filter = (
        "result",
        "review_required",
        "competition_discipline__competition",
        "competition_discipline__discipline",
        "board",
    )
    search_fields = (
        "question_number",
        "exam_context",
        "topic_subtopic",
        "source",
        "observation",
    )
