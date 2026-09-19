import unicodedata

from django.db import models
from django.db.models import Max


def normalize_discipline_name(value):
    normalized = unicodedata.normalize("NFKC", value or "")
    return " ".join(normalized.split()).casefold()


class ExamBoard(models.Model):
    name = models.CharField("nome", max_length=180, unique=True)
    acronym = models.CharField("sigla", max_length=40, unique=True)

    class Meta:
        ordering = ["acronym"]
        verbose_name = "banca"
        verbose_name_plural = "bancas"

    def __str__(self):
        return f"{self.acronym} — {self.name}"


class Discipline(models.Model):
    name = models.CharField(max_length=160, unique=True)
    normalized_name = models.CharField(max_length=160, unique=True, editable=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "disciplina"
        verbose_name_plural = "disciplinas"

    def save(self, *args, **kwargs):
        self.name = " ".join(self.name.split())
        self.normalized_name = normalize_discipline_name(self.name)
        super().save(*args, **kwargs)

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
    board = models.ForeignKey(
        ExamBoard,
        verbose_name="banca",
        on_delete=models.PROTECT,
        related_name="competitions",
        null=True,
        blank=True,
    )
    initial_salary = models.DecimalField(
        "salário inicial", max_digits=12, decimal_places=2, null=True, blank=True
    )
    benefits = models.TextField("benefícios", blank=True)
    fee = models.DecimalField(
        "taxa de inscrição", max_digits=8, decimal_places=2, null=True, blank=True
    )
    registration_start = models.DateField("início das inscrições", null=True, blank=True)
    registration_end = models.DateField("fim das inscrições", null=True, blank=True)
    exam_date = models.DateField("data da prova", null=True, blank=True)
    exam_time = models.TimeField("horário da prova", null=True, blank=True)
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
        HETEROIDENTIFICATION = "heteroidentification", "Heteroidentificação"
        BIOPSYCHOSOCIAL = "biopsychosocial", "Avaliação biopsicossocial"
        PHYSICAL = "physical", "Teste de aptidão física"
        MEDICAL = "medical", "Avaliação médica"
        PSYCHOLOGICAL = "psychological", "Avaliação psicológica"
        DOCUMENTS = "documents", "Verificação documental"
        TRAINING = "training", "Curso de formação"
        OTHER = "other", "Outra etapa"

    competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE, related_name="stages"
    )
    stage_type = models.CharField(
        "etapa", max_length=24, choices=StageType.choices, default=StageType.OBJECTIVE
    )
    position = models.PositiveIntegerField("posição", default=0, editable=False)
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
    requires_nonzero_each_discipline = models.BooleanField(
        "não pode zerar disciplina", default=False
    )
    details = models.TextField("detalhes / critérios", blank=True)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "etapa do concurso"
        verbose_name_plural = "etapas do concurso"

    def save(self, *args, **kwargs):
        if not self.position and self.competition_id:
            current_max = (
                CompetitionStage.objects.filter(competition_id=self.competition_id)
                .aggregate(max_position=Max("position"))
                .get("max_position")
                or 0
            )
            self.position = current_max + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.competition} — {self.get_stage_type_display()}"


class CompetitionDiscipline(models.Model):
    class KnowledgeArea(models.TextChoices):
        GENERAL = "general", "Conhecimentos Gerais"
        SPECIFIC = "specific", "Conhecimentos Específicos"

    class Priority(models.TextChoices):
        P1 = "P1", "P1"
        P2 = "P2", "P2"
        P3 = "P3", "P3"

    class QuestionCountKind(models.TextChoices):
        OFFICIAL = "official", "Oficial"
        ESTIMATED = "estimated", "Estimativa"

    competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE, related_name="discipline_links"
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
    question_count_kind = models.CharField(
        "origem do número de questões",
        max_length=12,
        choices=QuestionCountKind.choices,
        default=QuestionCountKind.OFFICIAL,
    )
    weight = models.DecimalField(
        "peso", max_digits=5, decimal_places=2, null=True, blank=True
    )
    max_score = models.DecimalField(
        "pontuação máxima", max_digits=8, decimal_places=2, null=True, blank=True
    )
    minimum_score = models.DecimalField(
        "pontuação mínima", max_digits=8, decimal_places=2, null=True, blank=True
    )
    position = models.PositiveIntegerField("posição", default=0, editable=False)

    class Meta:
        ordering = ["position", "discipline__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["competition", "discipline"],
                name="unique_competition_discipline",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.position and self.competition_id:
            current_max = (
                CompetitionDiscipline.objects.filter(competition_id=self.competition_id)
                .aggregate(max_position=Max("position"))
                .get("max_position")
                or 0
            )
            self.position = current_max + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.competition} — {self.discipline}"



class SyllabusItem(models.Model):
    competition_discipline = models.ForeignKey(
        CompetitionDiscipline,
        on_delete=models.CASCADE,
        related_name="syllabus_items",
        verbose_name="disciplina do concurso",
    )
    item_code = models.CharField(
        "item / código",
        max_length=40,
        blank=True,
        help_text="Numeração exatamente como aparece no edital, quando houver.",
    )
    content = models.TextField("conteúdo do edital")
    priority = models.CharField(
        "prioridade",
        max_length=2,
        choices=CompetitionDiscipline.Priority.choices,
        default=CompetitionDiscipline.Priority.P2,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="children",
        null=True,
        blank=True,
        verbose_name="item-pai",
    )
    position = models.PositiveIntegerField("posição", default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["competition_discipline__position", "position", "id"]
        verbose_name = "item do edital"
        verbose_name_plural = "itens do edital"

    def save(self, *args, **kwargs):
        if not self.position and self.competition_discipline_id:
            current_max = (
                SyllabusItem.objects.filter(
                    competition_discipline_id=self.competition_discipline_id
                )
                .aggregate(max_position=Max("position"))
                .get("max_position")
                or 0
            )
            self.position = current_max + 1
        super().save(*args, **kwargs)

    def __str__(self):
        prefix = f"{self.item_code} — " if self.item_code else ""
        preview = self.content.strip().replace("\n", " ")[:80]
        return f"{prefix}{preview}"
