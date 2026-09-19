from django import forms

from apps.studies.models import Lesson

from .models import QuestionRecord


class QuestionRecordForm(forms.ModelForm):
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
            "review_required": "Revisar?",
            "question_url": "URL da questão",
            "url_pending": "URL pendente de identificação",
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

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned = super().clean()
        lesson = cleaned.get("lesson")

        if (
            lesson
            and self.discipline_link
            and lesson.competition_discipline_id != self.discipline_link.pk
        ):
            self.add_error(
                "lesson",
                "Selecione somente uma aula desta disciplina.",
            )

        return cleaned

    def save(self, commit=True):
        record = super().save(commit=False)
        if not record.competition_discipline_id:
            record.competition_discipline = self.discipline_link
        if commit:
            record.full_clean()
            record.save()
        return record
