from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date

from apps.competitions.models import Competition, CompetitionDiscipline

from .forms import LessonForm
from .models import Lesson


def lesson_list(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    discipline_links = list(
        competition.discipline_links.select_related("discipline")
        .order_by("position", "discipline__name")
    )

    lessons = (
        Lesson.objects.filter(
            competition_discipline__competition=competition
        )
        .select_related("competition_discipline__discipline")
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

    selected_discipline_link = None
    if discipline_id.isdigit():
        selected_discipline_link = next(
            (
                link
                for link in discipline_links
                if link.pk == int(discipline_id)
            ),
            None,
        )
        if selected_discipline_link:
            lessons = lessons.filter(
                competition_discipline=selected_discipline_link
            )

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

    paginator = Paginator(lessons, 50)
    page_obj = paginator.get_page(request.GET.get("pagina"))
    pagination_query = request.GET.copy()
    pagination_query.pop("pagina", None)

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
            "lessons": page_obj.object_list,
            "page_obj": page_obj,
            "page_size": paginator.per_page,
            "pagination_query": pagination_query.urlencode(),
            "pagination_pages": paginator.get_elided_page_range(
                page_obj.number,
                on_each_side=2,
                on_ends=1,
            ),
            "pagination_ellipsis": paginator.ELLIPSIS,
            "discipline_links": discipline_links,
            "selected_discipline_link": selected_discipline_link,
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


def lesson_choose_discipline(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    discipline_links = list(
        competition.discipline_links.select_related("discipline")
        .order_by("position", "discipline__name")
    )
    return render(
        request,
        "studies/lesson_choose_discipline.html",
        {
            "competition": competition,
            "active_tab": "lessons",
            "discipline_links": discipline_links,
        },
    )


def lesson_create(request, pk, link_id):
    competition = get_object_or_404(Competition, pk=pk)
    discipline_link = get_object_or_404(
        CompetitionDiscipline.objects.select_related("discipline"),
        pk=link_id,
        competition=competition,
    )

    form = LessonForm(
        request.POST or None,
        discipline_link=discipline_link,
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
            "discipline_link": discipline_link,
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
    discipline_link = lesson.competition_discipline
    form = LessonForm(
        request.POST or None,
        instance=lesson,
        discipline_link=discipline_link,
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
            "discipline_link": discipline_link,
            "lesson": lesson,
            "form": form,
            "page_title": f"Editar {lesson.code}",
            "submit_label": "Salvar alterações",
        },
    )
