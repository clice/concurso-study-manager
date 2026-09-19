import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.competitions.models import Competition, normalize_discipline_name
from apps.studies.models import Lesson


DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "dataprev_2026_lessons"


class Command(BaseCommand):
    help = (
        "Importa as aulas do Cronograma DATAPREV 2026 para o banco local. "
        "O snapshot preserva disciplina, título, macrotema, materiais, planejamento, "
        "progresso, prática, observações e vínculo com o edital."
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
                "Atualiza aulas já vinculadas a uma referência de origem. "
                "Sem esta opção, registros já importados são preservados."
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
            raise CommandError("Nenhuma aula encontrada no snapshot de importação.")

        return rows

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

        links = list(
            competition.discipline_links.select_related("discipline").order_by("position")
        )
        links_by_name = {
            normalize_discipline_name(link.discipline.name): link
            for link in links
        }

        rows = self._load_rows()
        if requested_discipline:
            requested_key = normalize_discipline_name(requested_discipline)
            rows = [
                row
                for row in rows
                if normalize_discipline_name(row["discipline"]) == requested_key
            ]
            if not rows:
                raise CommandError(
                    f'Nenhuma aula encontrada para "{requested_discipline}".'
                )

        missing_disciplines = sorted(
            {
                row["discipline"]
                for row in rows
                if normalize_discipline_name(row["discipline"]) not in links_by_name
            }
        )
        if missing_disciplines:
            raise CommandError(
                "Disciplinas ausentes no concurso: " + ", ".join(missing_disciplines)
            )

        planned = {
            "create": 0,
            "adopt": 0,
            "refresh": 0,
            "skip": 0,
            "syllabus_links": 0,
            "syllabus_missing": 0,
        }

        position_by_link = {}
        operations = []

        for row in rows:
            link = links_by_name[normalize_discipline_name(row["discipline"])]
            position_by_link[link.pk] = position_by_link.get(link.pk, 0) + 1
            position = position_by_link[link.pk]

            existing = Lesson.objects.filter(
                source_reference=row["source_reference"]
            ).first()

            action = None
            if existing:
                if existing.competition_discipline.competition_id != competition.pk:
                    raise CommandError(
                        f'Referência {row["source_reference"]} já pertence a outro concurso.'
                    )
                action = "refresh" if refresh_existing else "skip"
            else:
                manual_match = Lesson.objects.filter(
                    competition_discipline=link,
                    source_reference__isnull=True,
                    title=row["title"],
                ).first()
                if manual_match:
                    existing = manual_match
                    action = "adopt"
                else:
                    action = "create"

            syllabus_item = None
            syllabus_item_code = row.get("syllabus_item_code")
            if syllabus_item_code:
                syllabus_item = link.syllabus_items.filter(
                    item_code=syllabus_item_code
                ).first()
                if syllabus_item:
                    planned["syllabus_links"] += 1
                else:
                    planned["syllabus_missing"] += 1

            planned[action] += 1
            operations.append(
                {
                    "row": row,
                    "link": link,
                    "lesson": existing,
                    "action": action,
                    "position": position,
                    "syllabus_item": syllabus_item,
                }
            )

        self.stdout.write(
            f"Aulas no snapshot: {len(rows)} | "
            f"criar: {planned['create']} | "
            f"adotar cadastro manual: {planned['adopt']} | "
            f"atualizar: {planned['refresh']} | "
            f"preservar existentes: {planned['skip']}"
        )
        self.stdout.write(
            f"Vínculos ao edital encontrados: {planned['syllabus_links']} | "
            f"sem correspondência: {planned['syllabus_missing']}"
        )

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry-run concluído; nada foi alterado."))
            return

        with transaction.atomic():
            for operation in operations:
                if operation["action"] == "skip":
                    continue

                row = operation["row"]
                lesson = operation["lesson"] or Lesson(
                    competition_discipline=operation["link"]
                )

                lesson.competition_discipline = operation["link"]
                lesson.source_reference = row["source_reference"]
                lesson.title = row["title"]
                lesson.macrotheme = row.get("macrotheme", "")
                lesson.source = row.get("source", "Gran Cursos Online")
                lesson.video_url = row.get("video_url", "")
                lesson.transcript_url = row.get("transcript_url", "")
                lesson.handout_url = row.get("handout_url", "")
                lesson.suggested_week = row.get("suggested_week")
                lesson.planned_date = row.get("planned_date")
                lesson.studied_date = row.get("studied_date")
                lesson.status = row.get("status", Lesson.Status.NOT_STARTED)
                lesson.questions_done = row.get("questions_done")
                lesson.correct_answers = row.get("correct_answers")
                lesson.notes = row.get("notes", "")
                lesson.position = operation["position"]
                lesson.full_clean(exclude=["source_reference"])
                lesson.save()

                syllabus_item = operation["syllabus_item"]
                if syllabus_item:
                    lesson.syllabus_items.set([syllabus_item])
                elif operation["action"] in {"create", "adopt", "refresh"}:
                    lesson.syllabus_items.clear()

        self.stdout.write(
            self.style.SUCCESS(
                "Importação concluída. "
                f"{planned['create']} criada(s), "
                f"{planned['adopt']} cadastro(s) manual(is) aproveitado(s), "
                f"{planned['refresh']} atualizada(s), "
                f"{planned['skip']} preservada(s)."
            )
        )
        if planned["syllabus_missing"]:
            self.stdout.write(
                self.style.WARNING(
                    f"{planned['syllabus_missing']} aula(s) ficaram sem vínculo automático "
                    "com o edital; os demais dados foram importados normalmente."
                )
            )
