from django.db import models


class Discipline(models.Model):
    name = models.CharField(max_length=160, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "disciplina"
        verbose_name_plural = "disciplinas"

    def __str__(self):
        return self.name


class Competition(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planejado"
        ACTIVE = "active", "Em estudo"
        COMPLETED = "completed", "Concluído"
        ARCHIVED = "archived", "Arquivado"

    name = models.CharField(max_length=200)
    organization = models.CharField(max_length=180)
    role = models.CharField(max_length=200)
    board = models.CharField("banca", max_length=120, blank=True)
    notice_number = models.CharField("edital", max_length=120, blank=True)
    initial_salary = models.DecimalField(
        "salário inicial", max_digits=12, decimal_places=2, null=True, blank=True
    )
    benefits = models.TextField("benefícios", blank=True)
    registration_start = models.DateTimeField("início das inscrições", null=True, blank=True)
    registration_end = models.DateTimeField("fim das inscrições", null=True, blank=True)
    exam_date = models.DateField("data da prova", null=True, blank=True)
    exam_time = models.TimeField("horário da prova", null=True, blank=True)
    fee = models.DecimalField("taxa", max_digits=8, decimal_places=2, null=True, blank=True)
    official_url = models.URLField("URL oficial", blank=True)
    notes = models.TextField("observações", blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    disciplines = models.ManyToManyField(
        Discipline,
        through="CompetitionDiscipline",
        related_name="competitions",
    )

    class Meta:
        ordering = ["exam_date", "name"]
        verbose_name = "concurso"
        verbose_name_plural = "concursos"

    def __str__(self):
        return f"{self.organization} — {self.role}"


class CompetitionDiscipline(models.Model):
    class KnowledgeArea(models.TextChoices):
        GENERAL = "general", "Conhecimentos Gerais"
        SPECIFIC = "specific", "Conhecimentos Específicos"

    class Priority(models.TextChoices):
        P1 = "P1", "P1"
        P2 = "P2", "P2"
        P3 = "P3", "P3"

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.PROTECT)
    knowledge_area = models.CharField(max_length=16, choices=KnowledgeArea.choices)
    priority = models.CharField(max_length=2, choices=Priority.choices, default=Priority.P2)
    expected_questions = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "discipline__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["competition", "discipline"],
                name="unique_competition_discipline",
            )
        ]

    def __str__(self):
        return f"{self.competition} — {self.discipline}"
