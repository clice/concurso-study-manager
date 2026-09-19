from django.contrib import admin

from .models import Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "title",
        "competition_discipline",
        "suggested_week",
        "planned_date",
        "studied_date",
        "status",
    )
    list_filter = (
        "status",
        "competition_discipline__competition",
        "competition_discipline__discipline",
    )
    search_fields = (
        "code",
        "title",
        "macrotheme",
        "notes",
    )
    filter_horizontal = ("syllabus_items",)
