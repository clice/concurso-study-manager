from django import forms
from django.db import transaction

from .models import Competition, CompetitionDiscipline, CompetitionStage, Discipline


class DateInput(forms.DateInput):
    input_type = "date"


class TimeInput(forms.TimeInput):
    input_type = "time"


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"


class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = [
            "name",
            "organization",
            "role",
            "notice_number",
            "board",
            "initial_salary",
            "benefits",
            "fee",
            "registration_start",
            "registration_end",
            "exam_date",
            "exam_time",
            "validity",
            "location",
            "official_url",
            "status",
            "notes",
        ]
        widgets = {
            "benefits": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 4}),
            "registration_start": DateTimeLocalInput(format="%Y-%m-%dT%H:%M"),
            "registration_end": DateTimeLocalInput(format="%Y-%m-%dT%H:%M"),
            "exam_date": DateInput(),
            "exam_time": TimeInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["registration_start"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["registration_end"].input_formats = ["%Y-%m-%dT%H:%M"]
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["status"].widget.attrs["class"] = "form-select"


class CompetitionStageForm(forms.ModelForm):
    class Meta:
        model = CompetitionStage
        fields = [
            "name",
            "stage_type",
            "position",
            "scheduled_date",
            "scheduled_time",
            "eliminatory",
            "classificatory",
            "max_score",
            "minimum_score",
            "details",
        ]
        widgets = {
            "scheduled_date": DateInput(),
            "scheduled_time": TimeInput(),
            "details": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {"eliminatory", "classificatory"}:
                field.widget.attrs["class"] = "form-check-input"
            elif name == "stage_type":
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs.setdefault("class", "form-control")


class CompetitionDisciplineForm(forms.ModelForm):
    discipline_name = forms.CharField(
        label="Disciplina",
        max_length=160,
        help_text="Comece a digitar para reutilizar uma disciplina já cadastrada ou informe uma nova.",
    )

    class Meta:
        model = CompetitionDiscipline
        fields = [
            "stage",
            "discipline_name",
            "knowledge_area",
            "priority",
            "expected_questions",
            "weight",
            "max_score",
            "position",
        ]

    def __init__(self, *args, competition=None, **kwargs):
        self.competition = competition
        super().__init__(*args, **kwargs)
        self.fields["stage"].queryset = CompetitionStage.objects.none()
        if competition:
            self.fields["stage"].queryset = competition.stages.order_by("position")
        for name, field in self.fields.items():
            if name in {"stage", "knowledge_area", "priority"}:
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs.setdefault("class", "form-control")
        self.fields["discipline_name"].widget.attrs["list"] = "discipline-options"

    def clean_stage(self):
        stage = self.cleaned_data["stage"]
        if self.competition and stage.competition_id != self.competition.id:
            raise forms.ValidationError("A etapa escolhida não pertence a este concurso.")
        return stage

    def clean_discipline_name(self):
        name = " ".join(self.cleaned_data["discipline_name"].split())
        if not name:
            raise forms.ValidationError("Informe uma disciplina.")
        return name

    @transaction.atomic
    def save(self, commit=True):
        name = self.cleaned_data["discipline_name"]
        discipline = Discipline.objects.filter(name__iexact=name).first()
        if discipline is None:
            discipline = Discipline.objects.create(name=name)

        instance = super().save(commit=False)
        instance.competition = self.competition
        instance.discipline = discipline
        if commit:
            instance.save()
        return instance
