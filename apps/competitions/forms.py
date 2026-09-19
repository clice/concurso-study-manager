from decimal import Decimal, InvalidOperation

from django import forms
from django.db import transaction

from .models import (
    Competition,
    CompetitionDiscipline,
    CompetitionStage,
    Discipline,
    SyllabusItem,
    normalize_discipline_name,
)


class DateInput(forms.DateInput):
    input_type = "date"


class TimeInput(forms.TimeInput):
    input_type = "time"


class BRLCurrencyField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.TextInput(
                attrs={
                    "class": "form-control money-input",
                    "inputmode": "numeric",
                    "autocomplete": "off",
                    "placeholder": "R$ 0,00",
                }
            ),
        )
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if value in (None, ""):
            return ""
        if isinstance(value, str) and ("R$" in value or "," in value):
            return value
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return value
        integer, decimal = f"{amount:.2f}".split(".")
        groups = []
        while integer:
            groups.append(integer[-3:])
            integer = integer[:-3]
        return f"R$ {'.'.join(reversed(groups))},{decimal}"

    def clean(self, value):
        value = super().clean(value)
        if not value:
            return None

        normalized = (
            value.replace("R$", "")
            .replace("\u00a0", "")
            .replace(" ", "")
            .replace(".", "")
            .replace(",", ".")
        )
        try:
            return Decimal(normalized).quantize(Decimal("0.01"))
        except InvalidOperation as exc:
            raise forms.ValidationError("Informe um valor monetário válido.") from exc


class CompetitionForm(forms.ModelForm):
    initial_salary = BRLCurrencyField(label="Salário inicial")
    fee = BRLCurrencyField(label="Taxa de inscrição")

    class Meta:
        model = Competition
        fields = [
            "name",
            "organization",
            "role",
            "board",
            "location",
            "status",
            "initial_salary",
            "fee",
            "registration_start",
            "registration_end",
            "benefits",
            "exam_date",
            "exam_time",
            "official_url",
            "notes",
        ]
        widgets = {
            "benefits": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 4}),
            "registration_start": DateInput(),
            "registration_end": DateInput(),
            "exam_date": DateInput(),
            "exam_time": TimeInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {"board", "status"}:
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs.setdefault("class", "form-control")


class CompetitionStageForm(forms.ModelForm):
    class Meta:
        model = CompetitionStage
        fields = [
            "stage_type",
            "scheduled_date",
            "scheduled_time",
            "max_score",
            "minimum_score",
            "eliminatory",
            "classificatory",
            "requires_nonzero_each_discipline",
            "details",
        ]
        widgets = {
            "scheduled_date": DateInput(),
            "scheduled_time": TimeInput(),
            "details": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "stage_type": "Etapa",
            "requires_nonzero_each_discipline": "Não pode zerar nenhuma disciplina",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {
                "eliminatory",
                "classificatory",
                "requires_nonzero_each_discipline",
            }:
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
            "discipline_name",
            "knowledge_area",
            "priority",
            "expected_questions",
            "question_count_kind",
            "weight",
            "max_score",
            "minimum_score",
        ]
        labels = {
            "question_count_kind": "Origem do nº de questões",
        }
        help_texts = {
            "question_count_kind": "Marque como estimativa quando a distribuição não vier oficialmente no edital.",
        }

    def __init__(self, *args, competition=None, **kwargs):
        self.competition = competition
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.discipline_id:
            self.fields["discipline_name"].initial = self.instance.discipline.name

        for name, field in self.fields.items():
            if name in {"knowledge_area", "priority", "question_count_kind"}:
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs.setdefault("class", "form-control")
        self.fields["discipline_name"].widget.attrs["list"] = "discipline-options"

    def clean_discipline_name(self):
        name = " ".join(self.cleaned_data["discipline_name"].split())
        if not name:
            raise forms.ValidationError("Informe uma disciplina.")
        return name

    @transaction.atomic
    def save(self, commit=True):
        name = self.cleaned_data["discipline_name"]
        normalized_name = normalize_discipline_name(name)
        discipline = Discipline.objects.filter(normalized_name=normalized_name).first()
        if discipline is None:
            discipline = Discipline.objects.create(name=name)

        instance = super().save(commit=False)
        instance.competition = self.competition
        instance.discipline = discipline
        if commit:
            instance.save()
        return instance



class SyllabusItemForm(forms.ModelForm):
    class Meta:
        model = SyllabusItem
        fields = [
            "item_code",
            "content",
            "priority",
            "parent",
        ]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Transcreva o conteúdo exatamente como aparece no edital.",
                }
            ),
        }
        labels = {
            "item_code": "Item / código",
            "parent": "Item-pai (opcional)",
        }

    def __init__(self, *args, discipline_link=None, **kwargs):
        self.discipline_link = discipline_link
        super().__init__(*args, **kwargs)

        self.fields["parent"].queryset = SyllabusItem.objects.none()
        if discipline_link:
            parent_queryset = discipline_link.syllabus_items.order_by("position")
            if self.instance and self.instance.pk:
                parent_queryset = parent_queryset.exclude(pk=self.instance.pk)
            self.fields["parent"].queryset = parent_queryset
            self.fields["priority"].initial = (
                self.instance.priority
                if self.instance and self.instance.pk
                else discipline_link.priority
            )

        for name, field in self.fields.items():
            if name in {"priority", "parent"}:
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")
        if parent and self.discipline_link:
            if parent.competition_discipline_id != self.discipline_link.id:
                raise forms.ValidationError(
                    "O item-pai precisa pertencer à mesma disciplina."
                )
        return parent

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.competition_discipline = self.discipline_link
        if commit:
            instance.save()
        return instance
