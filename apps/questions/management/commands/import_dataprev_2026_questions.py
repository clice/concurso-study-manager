import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.competitions.models import Competition, normalize_discipline_name
from apps.questions.models import QuestionRecord, is_supported_question_url
from apps.studies.models import Lesson


DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "dataprev_2026_questions"

DISCIPLINE_ALIASES = {
    normalize_discipline_name("Lingua Portuguesa"): normalize_discipline_name(
        "Língua Portuguesa"
    ),
}


class Command(BaseCommand):
    help = (
        "Importa as questões respondidas da aba Questões do Cronograma "
        "DATAPREV 2026 para o banco local."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--competition",
            default="DATAPREV 2026",
            help="Nome exato do concurso. Padrão: DATAPREV 2026.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Valida e mostra o plano sem gravar nada.",
        )
        parser.add_argument(
            "--discipline",
            help="Opcional: importa somente a disciplina informada.",
        )
        parser.add_argument(
            "--refresh-existing",
            action="store_true",
            help=(
                "Atualiza registros já vinculados à linha de origem da planilha. "
                "Sem esta opção, questões já importadas são preservadas."
            ),
        )

    def _load_rows(self):
        if not DATA_DIR.exists():
            raise CommandError(f"Diretório de dados não encontrado: {DATA_DIR}")

        rows = []
        for path in sorted(DATA_DIR.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, list):
                raise CommandError(f"Arquivo inválido: {path.name}")
            rows.extend(payload)

        if not rows:
            raise CommandError("Nenhuma questão encontrada no snapshot.")

        return rows

    @staticmethod
    def _discipline_key(value):
        key = normalize_discipline_name(value)
        return DISCIPLINE_ALIASES.get(key, key)

    def handle(self, *args, **options):
        competition_name = options["competition"]
        requested_discipline = options.get("discipline")
        dry_run = options["dry_run"]
        refresh_existing = options["refresh_existing"]

        try:
            competition = Competition.objects.get(name=competition_name)
        except Competition.DoesNotExist as exc:
            raise CommandError(
                f'Concurso "{competition_name}" não encontrado.'
            ) from exc
        except Competition.MultipleObjectsReturned as exc:
            raise CommandError(
                f'Existe mais de um concurso chamado "{competition_name}".'
            ) from exc

        discipline_links = list(
            competition.discipline_links.select_related("discipline")
            .order_by("position", "discipline__name")
        )
        links_by_name = {
            self._discipline_key(link.discipline.name): link
            for link in discipline_links
        }

        rows = self._load_rows()

        if requested_discipline:
            requested_key = self._discipline_key(requested_discipline)
            rows = [
                row
                for row in rows
                if self._discipline_key(row["discipline"]) == requested_key
            ]
            if not rows:
                raise CommandError(
                    f'Nenhuma questão encontrada para "{requested_discipline}".'
                )

        missing_disciplines = sorted(
            {
                row["discipline"]
                for row in rows
                if self._discipline_key(row["discipline"]) not in links_by_name
            }
        )
        if missing_disciplines:
            raise CommandError(
                "Disciplinas ausentes no concurso: "
                + ", ".join(missing_disciplines)
            )

        lesson_by_source = {
            lesson.source_reference: lesson
            for lesson in Lesson.objects.filter(
                competition_discipline__competition=competition,
                source_reference__isnull=False,
            ).select_related("competition_discipline")
        }

        planned = {
            "create": 0,
            "adopt": 0,
            "refresh": 0,
            "skip": 0,
            "lesson_linked": 0,
            "lesson_unlinked": 0,
            "lesson_mismatch": 0,
            "urls": 0,
            "url_pending": 0,
            "invalid_urls": 0,
        }
        operations = []

        for row in rows:
            link = links_by_name[self._discipline_key(row["discipline"])]

            existing = QuestionRecord.objects.filter(
                source_reference=row["source_reference"]
            ).first()

            if existing:
                if existing.competition_discipline.competition_id != competition.pk:
                    raise CommandError(
                        f'Referência {row["source_reference"]} já pertence '
                        "a outro concurso."
                    )
                action = "refresh" if refresh_existing else "skip"
            else:
                manual_match = QuestionRecord.objects.filter(
                    competition_discipline=link,
                    source_reference__isnull=True,
                    answered_date=row["answered_date"],
                    question_number=row["question_number"],
                    source=row.get("source", ""),
                    exam_context=row.get("exam_context", ""),
                ).first()

                if manual_match:
                    existing = manual_match
                    action = "adopt"
                else:
                    action = "create"

            lesson = None
            lesson_source_reference = row.get("lesson_source_reference")
            if lesson_source_reference:
                candidate = lesson_by_source.get(lesson_source_reference)
                if (
                    candidate
                    and candidate.competition_discipline_id == link.pk
                ):
                    lesson = candidate
                    planned["lesson_linked"] += 1
                else:
                    planned["lesson_mismatch"] += 1
            else:
                planned["lesson_unlinked"] += 1

            raw_question_url = (row.get("question_url") or "").strip()
            question_url = (
                raw_question_url
                if is_supported_question_url(raw_question_url)
                else ""
            )
            url_pending = not bool(question_url)

            if question_url:
                planned["urls"] += 1
            elif url_pending:
                planned["url_pending"] += 1
            if raw_question_url and not question_url:
                planned["invalid_urls"] += 1

            planned[action] += 1
            operations.append(
                {
                    "row": row,
                    "link": link,
                    "lesson": lesson,
                    "existing": existing,
                    "action": action,
                    "question_url": question_url,
                    "url_pending": url_pending,
                }
            )

        self.stdout.write(
            f"Questões no snapshot: {len(rows)} | "
            f"criar: {planned['create']} | "
            f"adotar cadastro manual: {planned['adopt']} | "
            f"atualizar: {planned['refresh']} | "
            f"preservar existentes: {planned['skip']}"
        )
        self.stdout.write(
            f"Vínculo seguro com aula: {planned['lesson_linked']} | "
            f"sem referência de aula: {planned['lesson_unlinked']} | "
            f"referência incompatível/não encontrada: {planned['lesson_mismatch']}"
        )
        self.stdout.write(
            f"URLs individuais do Gran identificadas: {planned['urls']} | "
            f"URLs pendentes de identificação: {planned['url_pending']} | "
            f"URLs descartadas por não serem links individuais do Gran: "
            f"{planned['invalid_urls']}"
        )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS("Dry-run concluído; nada foi alterado.")
            )
            return

        with transaction.atomic():
            for operation in operations:
                if operation["action"] == "skip":
                    continue

                row = operation["row"]
                record = operation["existing"] or QuestionRecord(
                    competition_discipline=operation["link"]
                )

                record.competition_discipline = operation["link"]
                record.lesson = operation["lesson"]
                record.source_reference = row["source_reference"]
                record.answered_date = row["answered_date"]
                record.board = row.get("board", "")
                record.exam_context = row.get("exam_context", "")
                record.question_number = row["question_number"]
                record.topic_subtopic = row.get("topic_subtopic", "")
                record.user_answer = row.get("user_answer", "")
                record.answer_key = row.get("answer_key", "")
                record.result = row["result"]
                record.source = row.get("source", "")
                record.observation = row.get("observation", "")
                record.review_required = row.get("review_required", False)
                record.last_review = row.get("last_review")
                record.next_review = row.get("next_review")
                record.review_status = row.get("review_status")
                record.question_url = operation["question_url"]
                record.url_pending = operation["url_pending"]
                record.full_clean()
                record.save()

        self.stdout.write(
            self.style.SUCCESS(
                "Importação concluída. "
                f"{planned['create']} criada(s), "
                f"{planned['adopt']} cadastro(s) manual(is) aproveitado(s), "
                f"{planned['refresh']} atualizada(s), "
                f"{planned['skip']} preservada(s)."
            )
        )

        if planned["lesson_mismatch"]:
            self.stdout.write(
                self.style.WARNING(
                    f"{planned['lesson_mismatch']} questão(ões) tinham referência "
                    "de aula que não pôde ser vinculada com segurança. "
                    "Elas foram importadas sem aula."
                )
            )
