from django.contrib import admin

from .models import (
    Competition,
    CompetitionDiscipline,
    CompetitionStage,
    Discipline,
    ExamBoard,
)


class CompetitionStageInline(admin.TabularInline):
    model = CompetitionStage
    extra = 0


class CompetitionDisciplineInline(admin.TabularInline):
    model = CompetitionDiscipline
    extra = 0


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("organization", "role", "board", "exam_date", "status")
    list_filter = ("status", "board")
    search_fields = ("organization", "role", "name")
    inlines = [CompetitionStageInline, CompetitionDisciplineInline]


@admin.register(CompetitionStage)
class CompetitionStageAdmin(admin.ModelAdmin):
    list_display = ("competition", "position", "stage_type", "scheduled_date")
    list_filter = ("stage_type", "eliminatory", "classificatory")


@admin.register(ExamBoard)
class ExamBoardAdmin(admin.ModelAdmin):
    list_display = ("acronym", "name")
    search_fields = ("acronym", "name")


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    search_fields = ("name",)
