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

    name = models.CharField("nome do concurso", max_length=200)
    organization = models.CharField("órgão", max_length=180)
    role = models.CharField("cargo", max_length=200)
    board = models.CharField("banca", max_length=120, blank=True)
    notice_number = models.CharField("edital", max_length=120, blank=True)
    initial_salary = models.DecimalField(
        "salário inicial", max_digits=12, decimal_places=2, null=True, blank=True
    )
    benefits = models.TextField("benefícios", blank=True)
    fee = models.DecimalField("taxa", max_digits=8, decimal_places=2, null=True, blank=True)
    registration_start = models.DateTimeField("início das inscrições", null=True, blank=True)
    registration_end = models.DateTimeField("fim das inscrições", null=True, blank=True)
    exam_date = models.DateField("data principal da prova", null=True, blank=True)
    exam_time = models.TimeField("horário principal da prova", null=True, blank=True)
    validity = models.CharField("validade", max_length=220, blank=True)
    location = models.CharField("localidade", max_length=220, blank=True)
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


class CompetitionStage(models.Model):
    class StageType(models.TextChoices):
        OBJECTIVE = "objective", "Prova objetiva"
        ESSAY = "essay", "Prova discursiva"
        PRACTICAL = "practical", "Prova prática"
        TITLES = "titles", "Avaliação de títulos"
        PHYSICAL = "physical", "Teste de aptidão física"
        MEDICAL = "medical", "Avaliação médica"
        PSYCHOLOGICAL = "psychological", "Avaliação psicológica"
        DOCUMENTS = "documents", "Verificação documental"
        TRAINING = "training", "Curso de formação"
        OTHER = "other", "Outra etapa"

    competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE, related_name="stages"
    )
    name = models.CharField("nome da etapa", max_length=180)
    stage_type = models.CharField(
        "tipo", max_length=24, choices=StageType.choices, default=StageType.OBJECTIVE
    )
    position = models.PositiveIntegerField(
        "posição", default=1, help_text="Ordem em que a etapa aparece no concurso."
    )
    scheduled_date = models.DateField("data", null=True, blank=True)
    scheduled_time = models.TimeField("horário", null=True, blank=True)
    eliminatory = models.BooleanField("eliminatória", default=True)
    classificatory = models.BooleanField("classificatória", default=True)
    max_score = models.DecimalField(
        "pontuação máxima", max_digits=8, decimal_places=2, null=True, blank=True
    )
    minimum_score = models.DecimalField(
        "pontuação mínima", max_digits=8, decimal_places=2, null=True, blank=True
    )
    details = models.TextField("detalhes / critérios", blank=True)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "etapa do concurso"
        verbose_name_plural = "etapas do concurso"
        constraints = [
            models.UniqueConstraint(
                fields=["competition", "position"],
                name="unique_competition_stage_position",
            )
        ]

    def __str__(self):
        return f"{self.competition} — {self.name}"


class CompetitionDiscipline(models.Model):
    class KnowledgeArea(models.TextChoices):
        GENERAL = "general", "Conhecimentos Gerais"
        SPECIFIC = "specific", "Conhecimentos Específicos"

    class Priority(models.TextChoices):
        P1 = "P1", "P1"
        P2 = "P2", "P2"
        P3 = "P3", "P3"

    competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE, related_name="discipline_links"
    )
    stage = models.ForeignKey(
        CompetitionStage,
        on_delete=models.CASCADE,
        related_name="discipline_links",
    )
    discipline = models.ForeignKey(Discipline, on_delete=models.PROTECT)
    knowledge_area = models.CharField(
        "grupo", max_length=16, choices=KnowledgeArea.choices
    )
    priority = models.CharField(
        "prioridade", max_length=2, choices=Priority.choices, default=Priority.P2
    )
    expected_questions = models.PositiveIntegerField(
        "número de questões", null=True, blank=True
    )
    weight = models.DecimalField(
        "peso", max_digits=5, decimal_places=2, null=True, blank=True
    )
    max_score = models.DecimalField(
        "pontuação máxima", max_digits=8, decimal_places=2, null=True, blank=True
    )
    position = models.PositiveIntegerField(
        "posição", default=1, help_text="Ordem de exibição dentro da etapa."
    )

    class Meta:
        ordering = ["stage__position", "position", "discipline__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["competition", "stage", "discipline"],
                name="unique_competition_stage_discipline",
            )
        ]

    def __str__(self):
        return f"{self.competition} — {self.stage} — {self.discipline}"
