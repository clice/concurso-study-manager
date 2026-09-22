import json

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.studies.models import Lesson

from .forms import (
    CompetitionDisciplineForm,
    CompetitionForm,
    CompetitionStageForm,
    SyllabusItemForm,
)
from .models import (
    Competition,
    CompetitionDiscipline,
    CompetitionStage,
    Discipline,
    SyllabusItem,
)


def _competition_or_404(pk):
    return get_object_or_404(Competition, pk=pk)


def _discipline_links(competition):
    return list(
        competition.discipline_links.select_related("discipline")
        .annotate(syllabus_item_count=Count("syllabus_items", distinct=True))
        .order_by("position", "discipline__name")
    )


def _overview_context(competition, **extra):
    stage_form = extra.pop("stage_form", None)
    if stage_form is None:
        stage_form = CompetitionStageForm()

    discipline_form = extra.pop("discipline_form", None)
    if discipline_form is None:
        discipline_form = CompetitionDisciplineForm(competition=competition)

    stage_form_overrides = extra.pop("stage_form_overrides", {})
    discipline_form_overrides = extra.pop("discipline_form_overrides", {})
    open_stage_id = extra.pop("open_stage_id", None)
    open_discipline_id = extra.pop("open_discipline_id", None)
    open_section = extra.pop("open_section", "")

    totals = competition.discipline_links.aggregate(
        total_questions=Sum("expected_questions"),
        total_max_score=Sum("max_score"),
    )
    has_estimates = competition.discipline_links.filter(
        expected_questions__isnull=False,
        question_count_kind=CompetitionDiscipline.QuestionCountKind.ESTIMATED,
    ).exists()

    stages = list(competition.stages.order_by("position", "id"))
    stage_rows = [
        {
            "stage": stage,
            "form": stage_form_overrides.get(stage.id)
            or CompetitionStageForm(instance=stage),
            "open": open_stage_id == stage.id,
        }
        for stage in stages
    ]

    discipline_links = _discipline_links(competition)
    discipline_rows = [
        {
            "link": link,
            "form": discipline_form_overrides.get(link.id)
            or CompetitionDisciplineForm(
                instance=link,
                competition=competition,
            ),
            "open": open_discipline_id == link.id,
        }
        for link in discipline_links
    ]

    days_to_exam = None
    if competition.exam_date:
        days_to_exam = (competition.exam_date - timezone.localdate()).days

    context = {
        "competition": competition,
        "active_tab": "overview",
        "discipline_links": discipline_links,
        "discipline_rows": discipline_rows,
        "discipline_count": len(discipline_links),
        "stage_rows": stage_rows,
        "stage_count": len(stages),
        "stage_form": stage_form,
        "discipline_form": discipline_form,
        "discipline_names": Discipline.objects.values_list(
            "name", flat=True
        ).order_by("name"),
        "open_section": open_section,
        "total_syllabus_items": sum(
            link.syllabus_item_count for link in discipline_links
        ),
        "total_questions": totals["total_questions"],
        "total_max_score": totals["total_max_score"],
        "has_estimates": has_estimates,
        "days_to_exam": days_to_exam,
    }
    context.update(extra)
    return context


def _structure_context(competition, **extra):
    context = {
        "competition": competition,
        "active_tab": "overview",
        "stage_form": CompetitionStageForm(),
        "discipline_form": CompetitionDisciplineForm(competition=competition),
        "discipline_names": Discipline.objects.values_list("name", flat=True).order_by("name"),
    }
    context.update(extra)
    return context


def _syllabus_context(competition, **extra):
    syllabus_form_overrides = extra.pop("syllabus_form_overrides", {})
    open_syllabus_link_id = extra.get("open_syllabus_link_id")
    discipline_links = list(
        competition.discipline_links.select_related("discipline")
        .prefetch_related("syllabus_items__parent")
        .order_by("position", "discipline__name")
    )

    syllabus_blocks = []
    total_syllabus_items = 0

    for link in discipline_links:
        items = list(link.syllabus_items.all())
        total_syllabus_items += len(items)
        syllabus_blocks.append(
            {
                "link": link,
                "items": items,
                "item_count": len(items),
                "form": syllabus_form_overrides.get(link.id)
                or SyllabusItemForm(
                    discipline_link=link,
                    prefix=f"syllabus-{link.id}",
                ),
                "open": open_syllabus_link_id == link.id,
            }
        )

    context = {
        "competition": competition,
        "active_tab": "syllabus",
        "syllabus_blocks": syllabus_blocks,
        "syllabus_discipline_count": len(discipline_links),
        "total_syllabus_items": total_syllabus_items,
    }
    context.update(extra)
    return context


def competition_create(request):
    form = CompetitionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        competition = form.save()
        messages.success(request, "Concurso cadastrado. Agora você pode incluir etapas e disciplinas.")
        return redirect("competitions:detail", pk=competition.pk)
    return render(
        request,
        "competitions/competition_form.html",
        {"form": form, "page_title": "Novo concurso"},
    )


def competition_edit(request, pk):
    competition = _competition_or_404(pk)
    form = CompetitionForm(request.POST or None, instance=competition)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Informações do concurso atualizadas.")
        return redirect("competitions:detail", pk=competition.pk)
    return render(
        request,
        "competitions/competition_form.html",
        {
            "form": form,
            "competition": competition,
            "page_title": "Editar concurso",
        },
    )


def competition_detail(request, pk):
    competition = get_object_or_404(
        Competition.objects.prefetch_related("stages"),
        pk=pk,
    )

    try:
        open_stage_id = int(request.GET.get("editar_etapa", ""))
    except (TypeError, ValueError):
        open_stage_id = None

    try:
        open_discipline_id = int(request.GET.get("editar_disciplina", ""))
    except (TypeError, ValueError):
        open_discipline_id = None

    return render(
        request,
        "competitions/competition_detail.html",
        _overview_context(
            competition,
            open_stage_id=open_stage_id,
            open_discipline_id=open_discipline_id,
        ),
    )


def competition_structure(request, pk):
    _competition_or_404(pk)
    return redirect("competitions:detail", pk=pk)


def competition_syllabus(request, pk):
    competition = _competition_or_404(pk)

    open_syllabus_link_id = request.GET.get("disciplina")
    try:
        open_syllabus_link_id = int(open_syllabus_link_id) if open_syllabus_link_id else None
    except (TypeError, ValueError):
        open_syllabus_link_id = None

    return render(
        request,
        "competitions/competition_syllabus.html",
        _syllabus_context(
            competition,
            open_syllabus_link_id=open_syllabus_link_id,
        ),
    )


def competition_dashboard(request, pk):
    competition = _competition_or_404(pk)
    lesson_qs = Lesson.objects.filter(
        competition_discipline__competition=competition
    )

    total_lessons = lesson_qs.count()
    completed_lessons = lesson_qs.filter(
        status=Lesson.Status.COMPLETED
    ).count()
    in_progress_lessons = lesson_qs.filter(
        status=Lesson.Status.IN_PROGRESS
    ).count()
    not_started_lessons = lesson_qs.filter(
        status=Lesson.Status.NOT_STARTED
    ).count()

    lesson_progress = (
        round((completed_lessons / total_lessons) * 100, 1)
        if total_lessons
        else 0
    )

    practice_totals = lesson_qs.aggregate(
        questions=Sum("questions_done"),
        correct=Sum("correct_answers"),
    )
    total_questions = practice_totals["questions"] or 0
    total_correct = practice_totals["correct"] or 0
    overall_accuracy = (
        round((total_correct / total_questions) * 100, 1)
        if total_questions
        else None
    )

    syllabus_qs = SyllabusItem.objects.filter(
        competition_discipline__competition=competition
    )
    total_syllabus_items = syllabus_qs.count()
    covered_syllabus_items = syllabus_qs.filter(
        lessons__competition_discipline__competition=competition
    ).distinct().count()
    syllabus_coverage = (
        round((covered_syllabus_items / total_syllabus_items) * 100, 1)
        if total_syllabus_items
        else 0
    )

    lesson_stats = {
        row["competition_discipline_id"]: row
        for row in (
            lesson_qs.values("competition_discipline_id")
            .annotate(
                total=Count("id"),
                completed=Count(
                    "id",
                    filter=Q(status=Lesson.Status.COMPLETED),
                ),
                in_progress=Count(
                    "id",
                    filter=Q(status=Lesson.Status.IN_PROGRESS),
                ),
                questions=Sum("questions_done"),
                correct=Sum("correct_answers"),
            )
        )
    }

    syllabus_stats = {
        row["competition_discipline_id"]: row
        for row in (
            syllabus_qs.values("competition_discipline_id")
            .annotate(
                total=Count("id", distinct=True),
                covered=Count(
                    "id",
                    filter=Q(lessons__isnull=False),
                    distinct=True,
                ),
            )
        )
    }

    discipline_rows = []
    for link in competition.discipline_links.select_related(
        "discipline"
    ).order_by("position", "discipline__name"):
        lesson_data = lesson_stats.get(link.pk, {})
        syllabus_data = syllabus_stats.get(link.pk, {})

        lessons_total = lesson_data.get("total", 0) or 0
        lessons_completed = lesson_data.get("completed", 0) or 0
        questions = lesson_data.get("questions", 0) or 0
        correct = lesson_data.get("correct", 0) or 0
        syllabus_total = syllabus_data.get("total", 0) or 0
        syllabus_covered = syllabus_data.get("covered", 0) or 0

        discipline_rows.append(
            {
                "id": link.pk,
                "name": link.discipline.name,
                "knowledge_area": link.get_knowledge_area_display(),
                "priority": link.priority,
                "lessons_total": lessons_total,
                "lessons_completed": lessons_completed,
                "lesson_progress": (
                    round((lessons_completed / lessons_total) * 100, 1)
                    if lessons_total
                    else 0
                ),
                "questions": questions,
                "correct": correct,
                "accuracy": (
                    round((correct / questions) * 100, 1)
                    if questions
                    else None
                ),
                "syllabus_total": syllabus_total,
                "syllabus_covered": syllabus_covered,
                "syllabus_coverage": (
                    round((syllabus_covered / syllabus_total) * 100, 1)
                    if syllabus_total
                    else 0
                ),
            }
        )

    weekly_rows = list(
        lesson_qs.filter(suggested_week__isnull=False)
        .values("suggested_week")
        .annotate(
            total=Count("id"),
            completed=Count(
                "id",
                filter=Q(status=Lesson.Status.COMPLETED),
            ),
        )
        .order_by("suggested_week")
    )

    days_to_exam = None
    if competition.exam_date:
        days_to_exam = (competition.exam_date - timezone.localdate()).days

    chart_data = {
        "disciplines": [row["name"] for row in discipline_rows],
        "lesson_progress": [row["lesson_progress"] for row in discipline_rows],
        "accuracy": [row["accuracy"] for row in discipline_rows],
        "syllabus_coverage": [
            row["syllabus_coverage"] for row in discipline_rows
        ],
        "status": {
            "labels": ["Concluídas", "Em andamento", "Não iniciadas"],
            "values": [
                completed_lessons,
                in_progress_lessons,
                not_started_lessons,
            ],
        },
        "weeks": {
            "labels": [
                f"Semana {row['suggested_week']}"
                for row in weekly_rows
            ],
            "total": [row["total"] for row in weekly_rows],
            "completed": [row["completed"] for row in weekly_rows],
        },
    }

    return render(
        request,
        "competitions/competition_dashboard.html",
        {
            "competition": competition,
            "active_tab": "dashboard",
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "in_progress_lessons": in_progress_lessons,
            "not_started_lessons": not_started_lessons,
            "lesson_progress": lesson_progress,
            "total_questions": total_questions,
            "total_correct": total_correct,
            "overall_accuracy": overall_accuracy,
            "total_syllabus_items": total_syllabus_items,
            "covered_syllabus_items": covered_syllabus_items,
            "syllabus_coverage": syllabus_coverage,
            "days_to_exam": days_to_exam,
            "discipline_rows": discipline_rows,
            "chart_data": chart_data,
        },
    )


def discipline_detail(request, pk, link_id):
    competition = _competition_or_404(pk)
    link = get_object_or_404(
        CompetitionDiscipline.objects.select_related("discipline"),
        pk=link_id,
        competition=competition,
    )
    syllabus_items = list(
        link.syllabus_items.select_related("parent").order_by("position", "id")
    )

    return render(
        request,
        "competitions/discipline_detail.html",
        {
            "competition": competition,
            "link": link,
            "syllabus_items": syllabus_items,
            "syllabus_item_count": len(syllabus_items),
            "lesson_count": link.lessons.count(),
            "active_tab": "overview",
            "edit_overview_url": (
                f'{reverse("competitions:detail", kwargs={"pk": competition.pk})}'
                f'?editar_disciplina={link.pk}#disciplinas'
            ),
        },
    )


def stage_add(request, pk):
    competition = _competition_or_404(pk)
    if request.method != "POST":
        return redirect(
            f'{reverse("competitions:detail", kwargs={"pk": pk})}#etapas'
        )

    form = CompetitionStageForm(request.POST)
    if form.is_valid():
        stage = form.save(commit=False)
        stage.competition = competition
        stage.save()
        messages.success(
            request,
            f'Etapa "{stage.get_stage_type_display()}" adicionada.',
        )
        return redirect(
            f'{reverse("competitions:detail", kwargs={"pk": pk})}#etapas'
        )

    return render(
        request,
        "competitions/competition_detail.html",
        _overview_context(
            competition,
            stage_form=form,
            open_section="stages",
        ),
    )


def stage_edit(request, pk, stage_id):
    competition = _competition_or_404(pk)
    stage = get_object_or_404(
        CompetitionStage,
        pk=stage_id,
        competition=competition,
    )

    if request.method != "POST":
        return redirect(
            f'{reverse("competitions:detail", kwargs={"pk": pk})}'
            f'?editar_etapa={stage.pk}#etapas'
        )

    form = CompetitionStageForm(request.POST, instance=stage)
    if form.is_valid():
        form.save()
        messages.success(
            request,
            f'Etapa "{stage.get_stage_type_display()}" atualizada.',
        )
        return redirect(
            f'{reverse("competitions:detail", kwargs={"pk": pk})}#etapas'
        )

    return render(
        request,
        "competitions/competition_detail.html",
        _overview_context(
            competition,
            stage_form_overrides={stage.id: form},
            open_stage_id=stage.id,
        ),
    )


def discipline_add(request, pk):
    competition = _competition_or_404(pk)
    if request.method != "POST":
        return redirect(
            f'{reverse("competitions:detail", kwargs={"pk": pk})}#disciplinas'
        )

    form = CompetitionDisciplineForm(request.POST, competition=competition)
    if form.is_valid():
        try:
            link = form.save()
        except IntegrityError:
            form.add_error(
                "discipline_name",
                "Essa disciplina já está associada a este concurso.",
            )
        else:
            messages.success(
                request,
                f'Disciplina "{link.discipline.name}" adicionada.',
            )
            return redirect(
                f'{reverse("competitions:detail", kwargs={"pk": pk})}#disciplinas'
            )

    return render(
        request,
        "competitions/competition_detail.html",
        _overview_context(
            competition,
            discipline_form=form,
            open_section="disciplines",
        ),
    )


def discipline_edit(request, pk, link_id):
    competition = _competition_or_404(pk)
    link = get_object_or_404(
        CompetitionDiscipline.objects.select_related("discipline"),
        pk=link_id,
        competition=competition,
    )

    if request.method != "POST":
        return redirect(
            f'{reverse("competitions:detail", kwargs={"pk": pk})}'
            f'?editar_disciplina={link.pk}#disciplinas'
        )

    form = CompetitionDisciplineForm(
        request.POST,
        instance=link,
        competition=competition,
    )

    if form.is_valid():
        try:
            updated = form.save()
        except IntegrityError:
            form.add_error(
                "discipline_name",
                "Essa disciplina já está associada a este concurso.",
            )
        else:
            messages.success(
                request,
                f'Disciplina "{updated.discipline.name}" atualizada.',
            )
            return redirect(
                f'{reverse("competitions:detail", kwargs={"pk": pk})}#disciplinas'
            )

    return render(
        request,
        "competitions/competition_detail.html",
        _overview_context(
            competition,
            discipline_form_overrides={link.id: form},
            open_discipline_id=link.id,
        ),
    )


def _requested_order(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        return [int(item_id) for item_id in payload.get("order", [])]
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


@require_POST
def stage_reorder(request, pk):
    competition = _competition_or_404(pk)
    requested = _requested_order(request)
    stages = list(competition.stages.order_by("position", "id"))
    current_ids = [stage.id for stage in stages]

    if requested is None or sorted(requested) != sorted(current_ids):
        return JsonResponse({"ok": False, "error": "Ordem de etapas inválida."}, status=400)

    by_id = {stage.id: stage for stage in stages}
    with transaction.atomic():
        for position, stage_id in enumerate(requested, start=1):
            by_id[stage_id].position = position
        CompetitionStage.objects.bulk_update(stages, ["position"])

    return JsonResponse({"ok": True})


@require_POST
def discipline_reorder(request, pk):
    competition = _competition_or_404(pk)
    requested = _requested_order(request)
    links = list(competition.discipline_links.order_by("position", "id"))
    current_ids = [link.id for link in links]

    if requested is None or sorted(requested) != sorted(current_ids):
        return JsonResponse({"ok": False, "error": "Ordem de disciplinas inválida."}, status=400)

    by_id = {link.id: link for link in links}
    with transaction.atomic():
        for position, link_id in enumerate(requested, start=1):
            by_id[link_id].position = position
        CompetitionDiscipline.objects.bulk_update(links, ["position"])

    return JsonResponse({"ok": True})


def syllabus_item_add(request, pk, link_id):
    competition = _competition_or_404(pk)
    link = get_object_or_404(
        CompetitionDiscipline.objects.select_related("discipline"),
        pk=link_id,
        competition=competition,
    )

    if request.method != "POST":
        return redirect(
            f'{reverse("competitions:syllabus", kwargs={"pk": pk})}?disciplina={link.pk}#edital-{link.pk}'
        )

    form = SyllabusItemForm(
        request.POST,
        discipline_link=link,
        prefix=f"syllabus-{link.id}",
    )

    if form.is_valid():
        item = form.save()
        label = item.item_code or "novo item"
        messages.success(
            request,
            f'Item "{label}" adicionado a {link.discipline.name}.',
        )
        return redirect(
            f'{reverse("competitions:syllabus", kwargs={"pk": pk})}?disciplina={link.pk}#edital-{link.pk}'
        )

    return render(
        request,
        "competitions/competition_syllabus.html",
        _syllabus_context(
            competition,
            syllabus_form_overrides={link.id: form},
            open_syllabus_link_id=link.id,
        ),
    )


def syllabus_item_edit(request, pk, item_id):
    competition = _competition_or_404(pk)
    item = get_object_or_404(
        SyllabusItem.objects.select_related(
            "competition_discipline__discipline",
            "competition_discipline__competition",
        ),
        pk=item_id,
        competition_discipline__competition=competition,
    )
    link = item.competition_discipline
    form = SyllabusItemForm(
        request.POST or None,
        instance=item,
        discipline_link=link,
    )

    if request.method == "POST" and form.is_valid():
        updated = form.save()
        messages.success(
            request,
            f'Item "{updated.item_code or "sem código"}" atualizado.',
        )
        return redirect(
            f'{reverse("competitions:syllabus", kwargs={"pk": pk})}?disciplina={link.pk}#edital-{link.pk}'
        )

    return render(
        request,
        "competitions/syllabus_item_form.html",
        {
            "competition": competition,
            "link": link,
            "item": item,
            "form": form,
        },
    )


@require_POST
def syllabus_item_reorder(request, pk, link_id):
    competition = _competition_or_404(pk)
    link = get_object_or_404(
        CompetitionDiscipline,
        pk=link_id,
        competition=competition,
    )
    requested = _requested_order(request)
    items = list(link.syllabus_items.order_by("position", "id"))
    current_ids = [item.id for item in items]

    if requested is None or sorted(requested) != sorted(current_ids):
        return JsonResponse(
            {"ok": False, "error": "Ordem dos itens do edital inválida."},
            status=400,
        )

    by_id = {item.id: item for item in items}
    with transaction.atomic():
        for position, item_id in enumerate(requested, start=1):
            by_id[item_id].position = position
        SyllabusItem.objects.bulk_update(items, ["position"])

    return JsonResponse({"ok": True})
