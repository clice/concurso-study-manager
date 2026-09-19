from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date

from apps.competitions.models import Competition, CompetitionDiscipline

from .forms import LessonForm
from .models import Lesson


def lesson_list(request, pk):
    competition = get_object_or_404(Competition, pk=pk)

    lessons = (
        Lesson.objects.filter(
            competition_discipline__competition=competition
        )
        .select_related("competition_discipline__discipline")
        .prefetch_related("syllabus_items")
        .order_by(
            "competition_discipline__position",
            "position",
            "id",
        )
    )

    discipline_id = request.GET.get("disciplina", "").strip()
    week = request.GET.get("semana", "").strip()
    planned_date = request.GET.get("data", "").strip()
    status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()

    if discipline_id.isdigit():
        lessons = lessons.filter(competition_discipline_id=int(discipline_id))

    if week.isdigit():
        lessons = lessons.filter(suggested_week=int(week))

    parsed_date = parse_date(planned_date) if planned_date else None
    if parsed_date:
        lessons = lessons.filter(planned_date=parsed_date)

    valid_statuses = {value for value, _ in Lesson.Status.choices}
    if status in valid_statuses:
        lessons = lessons.filter(status=status)

    if query:
        lessons = lessons.filter(
            Q(code__icontains=query)
            | Q(title__icontains=query)
            | Q(macrotheme__icontains=query)
            | Q(source__icontains=query)
        )

    lessons = list(lessons)
    filtered_total = len(lessons)
    completed_count = sum(
        lesson.status == Lesson.Status.COMPLETED for lesson in lessons
    )
    in_progress_count = sum(
        lesson.status == Lesson.Status.IN_PROGRESS for lesson in lessons
    )
    not_started_count = sum(
        lesson.status == Lesson.Status.NOT_STARTED for lesson in lessons
    )

    weeks = list(
        Lesson.objects.filter(
            competition_discipline__competition=competition,
            suggested_week__isnull=False,
        )
        .values_list("suggested_week", flat=True)
        .distinct()
        .order_by("suggested_week")
    )

    return render(
        request,
        "studies/lesson_list.html",
        {
            "competition": competition,
            "active_tab": "lessons",
            "lessons": lessons,
            "discipline_links": competition.discipline_links.select_related(
                "discipline"
            ).order_by("position", "discipline__name"),
            "weeks": weeks,
            "status_choices": Lesson.Status.choices,
            "filters": {
                "discipline": discipline_id,
                "week": week,
                "date": planned_date,
                "status": status,
                "q": query,
            },
            "filtered_total": filtered_total,
            "completed_count": completed_count,
            "in_progress_count": in_progress_count,
            "not_started_count": not_started_count,
        },
    )


def lesson_create(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    initial = {}

    discipline_id = request.GET.get("disciplina", "").strip()
    if discipline_id.isdigit():
        discipline_link = CompetitionDiscipline.objects.filter(
            pk=int(discipline_id),
            competition=competition,
        ).first()
        if discipline_link:
            initial["competition_discipline"] = discipline_link

    form = LessonForm(
        request.POST or None,
        competition=competition,
        initial=initial,
    )

    if request.method == "POST" and form.is_valid():
        lesson = form.save()
        return redirect(
            f'{reverse("studies:lesson_list", kwargs={"pk": competition.pk})}'
            f'?disciplina={lesson.competition_discipline_id}'
        )

    return render(
        request,
        "studies/lesson_form.html",
        {
            "competition": competition,
            "form": form,
            "page_title": "Nova aula",
            "submit_label": "Salvar aula",
        },
    )


def lesson_edit(request, pk, lesson_id):
    competition = get_object_or_404(Competition, pk=pk)
    lesson = get_object_or_404(
        Lesson.objects.select_related("competition_discipline__discipline"),
        pk=lesson_id,
        competition_discipline__competition=competition,
    )
    form = LessonForm(
        request.POST or None,
        instance=lesson,
        competition=competition,
    )

    if request.method == "POST" and form.is_valid():
        lesson = form.save()
        return redirect(
            f'{reverse("studies:lesson_list", kwargs={"pk": competition.pk})}'
            f'?disciplina={lesson.competition_discipline_id}'
        )

    return render(
        request,
        "studies/lesson_form.html",
        {
            "competition": competition,
            "lesson": lesson,
            "form": form,
            "page_title": f"Editar {lesson.code or 'aula'}",
            "submit_label": "Salvar alterações",
        },
    )
