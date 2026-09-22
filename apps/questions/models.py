import re

from django.core.exceptions import ValidationError
from django.db import models

from apps.competitions.models import CompetitionDiscipline
from apps.studies.models import Lesson


BOARD_ALIASES = {
    "CESPE": "CESPE/CEBRASPE",
    "CEBRASPE": "CESPE/CEBRASPE",
    "CESPE/CEBRASPE": "CESPE/CEBRASPE",
    "AVANÇA SP": "AVANÇA-SP",
    "AVANÇA-SP": "AVANÇA-SP",
    "AOCP": "AOCP",
    "INSTITUTO AOCP": "AOCP",
    "FUNDAÇÃO CETAP": "CETAP",
    "CETAP": "CETAP",
    "COMPERVE (UFRN)": "COMPERVE",
    "COMPERVE": "COMPERVE",
    "CPCON (UEPB)": "CPCON",
    "CPCON": "CPCON",
    "INSTITUTO CONSULPLAN": "CONSULPLAN",
    "CONSULPLAN": "CONSULPLAN",
    "OBJETIVA": "OBJETIVA CONCURSOS",
    "OBJETIVA CONCURSOS": "OBJETIVA CONCURSOS",
    "VUNESP-SP": "VUNESP",
    "VUNESP SP": "VUNESP",
    "VUNESP/SP": "VUNESP",
    "VUNESP": "VUNESP",
}


def normalize_board_name(value):
    """Padroniza banca em caixa alta e consolida aliases conhecidos."""
    board = re.sub(r"\s+", " ", (value or "").strip()).upper()
    if not board:
        return ""
    return BOARD_ALIASES.get(board, board)


QUESTION_URL_PATTERNS = (
    re.compile(
        r"^https?://questoes\.grancursosonline\.com\.br/"
        r"questoes-de-concursos/[^/?#]+/\d+/?(?:[?#].*)?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^https?://questoes\.grancursosonline\.com\.br/"
        r"prova/[^?#]+/\d+/?(?:[?#].*)?$",
        re.IGNORECASE,
    ),
)


def is_supported_question_url(value):
    """Retorna True somente para páginas individuais do Gran Questões."""
    url = (value or "").strip()
    if not url:
        return False
    return any(pattern.match(url) for pattern in QUESTION_URL_PATTERNS)


class QuestionRecord(models.Model):
    class Result(models.TextChoices):
        CORRECT = "correct", "Acerto"
        INCORRECT = "incorrect", "Erro"
        NOT_COUNTED = "not_counted", "Não contabilizar"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        COMPLETED = "completed", "Concluída"

    competition_discipline = models.ForeignKey(
        CompetitionDiscipline,
        on_delete=models.CASCADE,
        related_name="question_records",
        verbose_name="disciplina",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        related_name="question_records",
        null=True,
        blank=True,
        verbose_name="aula",
    )
    source_reference = models.CharField(
        "referência de origem",
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )
    code = models.CharField(
        "código",
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
    )
    answered_date = models.DateField("data")
    board = models.CharField("banca", max_length=120, blank=True)
    exam_context = models.CharField(
        "órgão / prova / cargo",
        max_length=300,
        blank=True,
    )
    question_number = models.CharField("questão", max_length=220)
    topic_subtopic = models.CharField(
        "tema / subtema",
        max_length=500,
        blank=True,
    )
    user_answer = models.CharField("resposta", max_length=300, blank=True)
    answer_key = models.CharField("gabarito", max_length=300, blank=True)
    result = models.CharField(
        "resultado",
        max_length=20,
        choices=Result.choices,
    )
    source = models.CharField("fonte", max_length=500, blank=True)
    observation = models.TextField("observação", blank=True)
    review_required = models.BooleanField("revisar?", default=False)
    last_review = models.DateField("última revisão", null=True, blank=True)
    next_review = models.DateField("próxima revisão", null=True, blank=True)
    review_status = models.CharField(
        "status da revisão",
        max_length=20,
        choices=ReviewStatus.choices,
        null=True,
        blank=True,
    )
    question_url = models.URLField("URL da questão", max_length=500, blank=True)
    url_pending = models.BooleanField(
        "URL pendente de identificação",
        default=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-answered_date", "-id"]
        verbose_name = "questão respondida"
        verbose_name_plural = "questões respondidas"

    @classmethod
    def next_code(cls):
        latest_code = (
            cls.objects.exclude(code="")
            .order_by("-id")
            .values_list("code", flat=True)
            .first()
        )
        if latest_code and latest_code.startswith("Q"):
            numeric = latest_code[1:]
            if numeric.isdigit():
                return f"Q{int(numeric) + 1:04d}"
        return "Q0001"

    @property
    def competition(self):
        return self.competition_discipline.competition

    @property
    def is_gran_url(self):
        return "grancursosonline.com.br" in (self.question_url or "")

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.next_code()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self.board = normalize_board_name(self.board)

        if self.lesson_id:
            if (
                self.competition_discipline_id
                and self.lesson.competition_discipline_id
                != self.competition_discipline_id
            ):
                raise ValidationError(
                    {"lesson": "A aula deve pertencer à mesma disciplina da questão."}
                )

        if self.url_pending and self.question_url:
            raise ValidationError(
                {
                    "question_url": (
                        "Informe a URL ou marque que ela está pendente, não os dois."
                    )
                }
            )

        if self.question_url and not is_supported_question_url(self.question_url):
            raise ValidationError(
                {
                    "question_url": (
                        "Use somente o link individual da questão no Gran Questões. "
                        "Links de outros bancos, degravação, Drive, PDF, prova completa, "
                        "legislação ou listagem devem ficar como URL Gran pendente."
                    )
                }
            )

        if self.review_status and not self.review_required:
            raise ValidationError(
                {
                    "review_status": (
                        "O status de revisão só deve ser usado quando a questão "
                        "estiver marcada para revisar."
                    )
                }
            )

    def __str__(self):
        return f"{self.code} — {self.competition_discipline.discipline.name}"
