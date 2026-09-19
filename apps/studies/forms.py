from django import forms

from apps.competitions.models import CompetitionDiscipline, SyllabusItem

from .models import Lesson


class SyllabusItemsField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        discipline = obj.competition_discipline.discipline.name
        return f"{discipline} · {obj.item_code} — {obj.content[:110]}"


class LessonForm(forms.ModelForm):
    syllabus_items = SyllabusItemsField(
        queryset=SyllabusItem.objects.none(),
        required=False,
        label="Itens do edital",
        help_text=(
            "Opcional. Selecione um ou mais itens do edital cobertos por esta aula. "
            "Use Ctrl/Cmd para selecionar vários."
        ),
    )

    class Meta:
        model = Lesson
        fields = [
            "competition_discipline",
            "code",
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
            "syllabus_items": forms.SelectMultiple(attrs={"size": 7}),
        }
        labels = {
            "competition_discipline": "Disciplina",
            "code": "ID da aula",
            "source": "Fonte / curso",
            "video_url": "URL da videoaula",
            "transcript_url": "URL da degravação",
            "handout_url": "URL da apostila",
        }
        help_texts = {
            "code": "Ex.: G588. Deixe vazio se a aula não tiver identificador.",
            "macrotheme": "Agrupamento do conteúdo usado no curso/cronograma.",
        }

    def __init__(self, *args, competition=None, **kwargs):
        self.competition = competition
        super().__init__(*args, **kwargs)

        discipline_queryset = CompetitionDiscipline.objects.none()
        syllabus_queryset = SyllabusItem.objects.none()

        if competition:
            discipline_queryset = competition.discipline_links.select_related(
                "discipline"
            ).order_by("position", "discipline__name")
            syllabus_queryset = SyllabusItem.objects.filter(
                competition_discipline__competition=competition
            ).select_related(
                "competition_discipline__discipline"
            ).order_by(
                "competition_discipline__position",
                "position",
            )

        self.fields["competition_discipline"].queryset = discipline_queryset
        self.fields["syllabus_items"].queryset = syllabus_queryset

        for name, field in self.fields.items():
            if name in {"competition_discipline", "status", "syllabus_items"}:
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned = super().clean()
        discipline_link = cleaned.get("competition_discipline")
        syllabus_items = cleaned.get("syllabus_items")
        questions_done = cleaned.get("questions_done")
        correct_answers = cleaned.get("correct_answers")

        if discipline_link and syllabus_items:
            invalid = syllabus_items.exclude(
                competition_discipline=discipline_link
            )
            if invalid.exists():
                self.add_error(
                    "syllabus_items",
                    "Selecione somente itens do edital pertencentes à disciplina escolhida.",
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
