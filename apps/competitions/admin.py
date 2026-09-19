from django.contrib import admin
from .models import Competition, CompetitionDiscipline, Discipline


class CompetitionDisciplineInline(admin.TabularInline):
    model = CompetitionDiscipline
    extra = 1


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("organization", "role", "board", "exam_date", "status")
    list_filter = ("status", "board")
    search_fields = ("organization", "role", "name")
    inlines = [CompetitionDisciplineInline]


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    search_fields = ("name",)
