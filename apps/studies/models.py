from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max

from apps.competitions.models import CompetitionDiscipline, SyllabusItem


class Lesson(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Não iniciada"
        IN_PROGRESS = "in_progress", "Em andamento"
        COMPLETED = "completed", "Concluída"

    competition_discipline = models.ForeignKey(
        CompetitionDiscipline,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="disciplina",
    )
    code = models.CharField(
        "código",
        max_length=40,
        blank=True,
        help_text="Identificador da aula no curso, por exemplo G588.",
    )
    title = models.CharField("título", max_length=300)
    macrotheme = models.CharField("macrotema", max_length=220, blank=True)
    syllabus_items = models.ManyToManyField(
        SyllabusItem,
        related_name="lessons",
        blank=True,
        verbose_name="itens do edital",
    )
    source = models.CharField(
        "fonte",
        max_length=120,
        default="Gran Cursos Online",
        blank=True,
    )
    video_url = models.URLField("videoaula", blank=True)
    transcript_url = models.URLField("degravação", blank=True)
    handout_url = models.URLField("apostila", blank=True)
    suggested_week = models.PositiveIntegerField(
        "semana sugerida",
        null=True,
        blank=True,
    )
    planned_date = models.DateField("data planejada", null=True, blank=True)
    studied_date = models.DateField("data estudada", null=True, blank=True)
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    questions_done = models.PositiveIntegerField(
        "questões feitas",
        null=True,
        blank=True,
    )
    correct_answers = models.PositiveIntegerField(
        "acertos",
        null=True,
        blank=True,
    )
    notes = models.TextField("observações", blank=True)
    position = models.PositiveIntegerField("posição", default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "competition_discipline__position",
            "position",
            "id",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["competition_discipline", "code"],
                condition=~models.Q(code=""),
                name="unique_lesson_code_per_competition_discipline",
            )
        ]
        verbose_name = "aula"
        verbose_name_plural = "aulas"

    @property
    def accuracy(self):
        if not self.questions_done:
            return None
        if self.correct_answers is None:
            return None
        return (self.correct_answers / self.questions_done) * 100

    @property
    def competition(self):
        return self.competition_discipline.competition

    def clean(self):
        super().clean()
        if (
            self.questions_done is not None
            and self.correct_answers is not None
            and self.correct_answers > self.questions_done
        ):
            raise ValidationError(
                {"correct_answers": "Os acertos não podem superar as questões feitas."}
            )

    def save(self, *args, **kwargs):
        if not self.position and self.competition_discipline_id:
            current_max = (
                Lesson.objects.filter(
                    competition_discipline_id=self.competition_discipline_id
                )
                .aggregate(max_position=Max("position"))
                .get("max_position")
                or 0
            )
            self.position = current_max + 1
        super().save(*args, **kwargs)

    def __str__(self):
        prefix = f"{self.code} — " if self.code else ""
        return f"{prefix}{self.title}"
