from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CompetitionDisciplineForm, CompetitionForm, CompetitionStageForm
from .models import Competition, CompetitionDiscipline, Discipline


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
            "discipline_links__stage",
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
        try:
            stage.save()
        except IntegrityError:
            form.add_error("position", "Já existe uma etapa nessa posição.")
        else:
            messages.success(request, f'Etapa "{stage.name}" adicionada.')
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
            form.add_error("discipline_name", "Essa disciplina já está associada a essa etapa.")
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
