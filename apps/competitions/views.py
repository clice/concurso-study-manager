import json

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

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
    competition = get_object_or_404(Competition, pk=pk)
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


def _competition_detail_context(competition, **extra):
    discipline_names = Discipline.objects.values_list("name", flat=True).order_by("name")
    totals = competition.discipline_links.aggregate(
        total_questions=Sum("expected_questions"),
        total_max_score=Sum("max_score"),
    )
    has_estimates = competition.discipline_links.filter(
        expected_questions__isnull=False,
        question_count_kind=CompetitionDiscipline.QuestionCountKind.ESTIMATED,
    ).exists()

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
        "stage_form": CompetitionStageForm(),
        "discipline_form": CompetitionDisciplineForm(competition=competition),
        "discipline_names": discipline_names,
        "total_questions": totals["total_questions"],
        "total_max_score": totals["total_max_score"],
        "has_estimates": has_estimates,
        "syllabus_blocks": syllabus_blocks,
        "syllabus_discipline_count": len(discipline_links),
        "total_syllabus_items": total_syllabus_items,
    }
    context.update(extra)
    return context


def competition_detail(request, pk):
    competition = get_object_or_404(
        Competition.objects.prefetch_related(
            "stages",
            "discipline_links__discipline",
        ),
        pk=pk,
    )
    return render(
        request,
        "competitions/competition_detail.html",
        _competition_detail_context(competition),
    )


def stage_add(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    if request.method != "POST":
        return redirect("competitions:detail", pk=pk)

    form = CompetitionStageForm(request.POST)
    if form.is_valid():
        stage = form.save(commit=False)
        stage.competition = competition
        stage.save()
        messages.success(request, f'Etapa "{stage.get_stage_type_display()}" adicionada.')
        return redirect(f'{reverse("competitions:detail", kwargs={"pk": pk})}#etapas')

    return render(
        request,
        "competitions/competition_detail.html",
        _competition_detail_context(
            competition,
            stage_form=form,
            open_section="stages",
        ),
    )


def stage_edit(request, pk, stage_id):
    competition = get_object_or_404(Competition, pk=pk)
    stage = get_object_or_404(
        CompetitionStage,
        pk=stage_id,
        competition=competition,
    )
    form = CompetitionStageForm(request.POST or None, instance=stage)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Etapa "{stage.get_stage_type_display()}" atualizada.')
        return redirect(f'{reverse("competitions:detail", kwargs={"pk": pk})}#etapas')

    return render(
        request,
        "competitions/stage_form.html",
        {
            "competition": competition,
            "stage": stage,
            "form": form,
        },
    )


def discipline_add(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    if request.method != "POST":
        return redirect("competitions:detail", pk=pk)

    form = CompetitionDisciplineForm(request.POST, competition=competition)
    if form.is_valid():
        try:
            link = form.save()
        except IntegrityError:
            form.add_error("discipline_name", "Essa disciplina já está associada a este concurso.")
        else:
            messages.success(request, f'Disciplina "{link.discipline.name}" adicionada.')
            return redirect(f'{reverse("competitions:detail", kwargs={"pk": pk})}#disciplinas')

    return render(
        request,
        "competitions/competition_detail.html",
        _competition_detail_context(
            competition,
            discipline_form=form,
            open_section="disciplines",
        ),
    )


def discipline_edit(request, pk, link_id):
    competition = get_object_or_404(Competition, pk=pk)
    link = get_object_or_404(
        CompetitionDiscipline.objects.select_related("discipline"),
        pk=link_id,
        competition=competition,
    )
    form = CompetitionDisciplineForm(
        request.POST or None,
        instance=link,
        competition=competition,
    )

    if request.method == "POST" and form.is_valid():
        try:
            updated = form.save()
        except IntegrityError:
            form.add_error("discipline_name", "Essa disciplina já está associada a este concurso.")
        else:
            messages.success(request, f'Disciplina "{updated.discipline.name}" atualizada.')
            return redirect(f'{reverse("competitions:detail", kwargs={"pk": pk})}#disciplinas')

    return render(
        request,
        "competitions/discipline_form.html",
        {
            "competition": competition,
            "link": link,
            "form": form,
            "discipline_names": Discipline.objects.values_list("name", flat=True).order_by("name"),
        },
    )


def _requested_order(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        return [int(item_id) for item_id in payload.get("order", [])]
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


@require_POST
def stage_reorder(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
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
    competition = get_object_or_404(Competition, pk=pk)
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
    competition = get_object_or_404(Competition, pk=pk)
    link = get_object_or_404(
        CompetitionDiscipline.objects.select_related("discipline"),
        pk=link_id,
        competition=competition,
    )

    if request.method != "POST":
        return redirect(
            f'{reverse("competitions:detail", kwargs={"pk": pk})}#edital-{link.pk}'
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
            f'{reverse("competitions:detail", kwargs={"pk": pk})}#edital-{link.pk}'
        )

    return render(
        request,
        "competitions/competition_detail.html",
        _competition_detail_context(
            competition,
            syllabus_form_overrides={link.id: form},
            open_section="syllabus",
            open_syllabus_link_id=link.id,
        ),
    )


def syllabus_item_edit(request, pk, item_id):
    competition = get_object_or_404(Competition, pk=pk)
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
            f'{reverse("competitions:detail", kwargs={"pk": pk})}#edital-{link.pk}'
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
    competition = get_object_or_404(Competition, pk=pk)
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
