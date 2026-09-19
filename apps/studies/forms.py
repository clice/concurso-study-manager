from django import forms

from apps.competitions.models import SyllabusItem

from .models import Lesson


class SyllabusItemsField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.item_code} — {obj.content[:135]}"


class LessonForm(forms.ModelForm):
    syllabus_items = SyllabusItemsField(
        queryset=SyllabusItem.objects.none(),
        required=False,
        label="Itens do edital",
        help_text="Opcional. Marque todos os itens do edital cobertos por esta aula.",
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Lesson
        fields = [
            "title",
            "macrotheme",
            "syllabus_items",
            "source",
            "suggested_week",
            "planned_date",
            "studied_date",
            "status",
            "video_url",
            "transcript_url",
            "handout_url",
            "questions_done",
            "correct_answers",
            "notes",
        ]
        widgets = {
            "planned_date": forms.DateInput(attrs={"type": "date"}),
            "studied_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "source": "Fonte / curso",
            "video_url": "URL da videoaula",
            "transcript_url": "URL da degravação",
            "handout_url": "URL da apostila",
        }
        help_texts = {
            "macrotheme": "Agrupamento do conteúdo usado no curso/cronograma.",
        }

    def __init__(self, *args, discipline_link=None, **kwargs):
        self.discipline_link = discipline_link
        super().__init__(*args, **kwargs)

        syllabus_queryset = SyllabusItem.objects.none()
        if discipline_link:
            syllabus_queryset = (
                discipline_link.syllabus_items.select_related("parent")
                .order_by("position", "id")
            )
        self.fields["syllabus_items"].queryset = syllabus_queryset

        for name, field in self.fields.items():
            if name == "status":
                field.widget.attrs["class"] = "form-select"
            elif name == "syllabus_items":
                field.widget.attrs["class"] = "syllabus-checkboxes"
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned = super().clean()
        syllabus_items = cleaned.get("syllabus_items")
        questions_done = cleaned.get("questions_done")
        correct_answers = cleaned.get("correct_answers")

        if self.discipline_link and syllabus_items:
            invalid = syllabus_items.exclude(
                competition_discipline=self.discipline_link
            )
            if invalid.exists():
                self.add_error(
                    "syllabus_items",
                    "Selecione somente itens do edital desta disciplina.",
                )

        if (
            questions_done is not None
            and correct_answers is not None
            and correct_answers > questions_done
        ):
            self.add_error(
                "correct_answers",
                "Os acertos não podem superar as questões feitas.",
            )

        return cleaned

    def save(self, commit=True):
        lesson = super().save(commit=False)
        if not lesson.competition_discipline_id:
            lesson.competition_discipline = self.discipline_link
        if commit:
            lesson.save()
            self.save_m2m()
        return lesson
