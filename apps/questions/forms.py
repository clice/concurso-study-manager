from django import forms

from apps.studies.models import Lesson

from .models import QuestionRecord


OTHER_BOARD_VALUE = "__other__"


class QuestionRecordForm(forms.ModelForm):
    board_other = forms.CharField(
        required=False,
        label="Outra banca",
        help_text="Use somente quando a banca ainda não estiver na lista.",
    )

    class Meta:
        model = QuestionRecord
        fields = [
            "lesson",
            "answered_date",
            "board",
            "exam_context",
            "question_number",
            "topic_subtopic",
            "user_answer",
            "answer_key",
            "result",
            "source",
            "observation",
            "review_required",
            "last_review",
            "next_review",
            "review_status",
            "question_url",
            "url_pending",
        ]
        widgets = {
            "answered_date": forms.DateInput(attrs={"type": "date"}),
            "last_review": forms.DateInput(attrs={"type": "date"}),
            "next_review": forms.DateInput(attrs={"type": "date"}),
            "observation": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "exam_context": "Órgão / prova / cargo",
            "topic_subtopic": "Tema / subtema",
            "user_answer": "Sua resposta",
            "answer_key": "Gabarito",
            "source": "Fonte / origem",
            "review_required": "Marcar para revisão",
            "question_url": "URL da questão",
            "url_pending": "URL pendente de identificação",
        }
        help_texts = {
            "source": (
                "Onde a questão foi usada ou localizada no estudo. "
                "Ex.: Slides G588 — 6 - JUnit II, Degravação 47 — Conjunções "
                "ou Gran Questões — curadoria. A URL individual fica no campo próprio."
            ),
        }

    def __init__(self, *args, discipline_link=None, lesson=None, **kwargs):
        self.discipline_link = discipline_link
        super().__init__(*args, **kwargs)

        self.fields["lesson"].queryset = Lesson.objects.none()
        if discipline_link:
            self.fields["lesson"].queryset = (
                Lesson.objects.filter(competition_discipline=discipline_link)
                .order_by("position", "id")
            )

        if lesson and not self.is_bound:
            self.initial["lesson"] = lesson.pk

        board_values = set(
            QuestionRecord.objects.exclude(board="")
            .values_list("board", flat=True)
            .distinct()
        )

        if discipline_link and discipline_link.competition.board:
            board_values.add(discipline_link.competition.board.acronym)

        current_board = ""
        if self.instance and self.instance.pk:
            current_board = self.instance.board or ""
            if current_board:
                board_values.add(current_board)

        board_choices = [("", "Selecione a banca")]
        board_choices.extend(
            (value, value)
            for value in sorted(board_values, key=str.casefold)
        )
        board_choices.append((OTHER_BOARD_VALUE, "Outra banca…"))

        self.fields["board"] = forms.ChoiceField(
            required=False,
            label="Banca",
            choices=board_choices,
            initial=current_board,
            widget=forms.Select(
                attrs={
                    "class": "form-select",
                    "data-question-board-select": "",
                }
            ),
        )
        self.fields["board_other"].widget.attrs.update(
            {
                "class": "form-control",
                "data-question-board-other-input": "",
            }
        )

        for name, field in self.fields.items():
            if name in {"board", "board_other"}:
                continue
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned = super().clean()
        lesson = cleaned.get("lesson")
        board = cleaned.get("board", "")
        board_other = (cleaned.get("board_other") or "").strip()

        if (
            lesson
            and self.discipline_link
            and lesson.competition_discipline_id != self.discipline_link.pk
        ):
            self.add_error(
                "lesson",
                "Selecione somente uma aula desta disciplina.",
            )

        if board == OTHER_BOARD_VALUE:
            if not board_other:
                self.add_error(
                    "board_other",
                    "Informe o nome da banca.",
                )
            else:
                cleaned["board"] = board_other

        return cleaned

    def save(self, commit=True):
        record = super().save(commit=False)
        if not record.competition_discipline_id:
            record.competition_discipline = self.discipline_link

        selected_board = self.cleaned_data.get("board", "")
        if selected_board:
            record.board = selected_board

        if commit:
            record.full_clean()
            record.save()
        return record
