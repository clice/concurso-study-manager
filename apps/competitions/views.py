import json

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CompetitionDisciplineForm, CompetitionForm, CompetitionStageForm
from .models import Competition, CompetitionDiscipline, CompetitionStage, Discipline


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


def competition_detail(request, pk):
    competition = get_object_or_404(
        Competition.objects.prefetch_related(
            "stages",
            "discipline_links__discipline",
        ),
        pk=pk,
    )
    discipline_names = Discipline.objects.values_list("name", flat=True).order_by("name")
    return render(
        request,
        "competitions/competition_detail.html",
        {
            "competition": competition,
            "stage_form": CompetitionStageForm(),
            "discipline_form": CompetitionDisciplineForm(competition=competition),
            "discipline_names": discipline_names,
        },
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
        {
            "competition": competition,
            "stage_form": form,
            "discipline_form": CompetitionDisciplineForm(competition=competition),
            "discipline_names": Discipline.objects.values_list("name", flat=True).order_by("name"),
            "open_section": "stages",
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
        {
            "competition": competition,
            "stage_form": CompetitionStageForm(),
            "discipline_form": form,
            "discipline_names": Discipline.objects.values_list("name", flat=True).order_by("name"),
            "open_section": "disciplines",
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
