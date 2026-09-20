from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.competitions.models import Competition
from apps.questions.models import QuestionRecord, is_supported_question_url


class Command(BaseCommand):
    help = (
        "Audita URLs de questões e, com --fix, remove links que não apontam "
        "para páginas individuais de questões."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--competition",
            help="Opcional: nome exato do concurso a auditar.",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help=(
                "Limpa URLs inválidas e marca os registros como URL pendente. "
                "Sem esta opção, apenas mostra o diagnóstico."
            ),
        )

    def handle(self, *args, **options):
        queryset = QuestionRecord.objects.exclude(question_url="").select_related(
            "competition_discipline__competition",
            "competition_discipline__discipline",
        )

        competition_name = options.get("competition")
        if competition_name:
            try:
                competition = Competition.objects.get(name=competition_name)
            except Competition.DoesNotExist as exc:
                raise CommandError(
                    f'Concurso "{competition_name}" não encontrado.'
                ) from exc
            queryset = queryset.filter(
                competition_discipline__competition=competition
            )

        records = list(queryset.order_by("id"))
        invalid = [
            record
            for record in records
            if not is_supported_question_url(record.question_url)
        ]
        valid_count = len(records) - len(invalid)

        self.stdout.write(
            f"URLs preenchidas: {len(records)} | "
            f"páginas individuais válidas: {valid_count} | "
            f"links inválidos para o campo: {len(invalid)}"
        )

        for record in invalid[:25]:
            self.stdout.write(
                f"- {record.code} | "
                f"{record.competition_discipline.discipline.name} | "
                f"{record.question_url}"
            )

        if len(invalid) > 25:
            self.stdout.write(
                f"... e mais {len(invalid) - 25} link(s) inválido(s)."
            )

        if not options["fix"]:
            self.stdout.write(
                "Auditoria concluída sem alterações. Use --fix para corrigir."
            )
            return

        with transaction.atomic():
            for record in invalid:
                record.question_url = ""
                record.url_pending = True
                record.save(
                    update_fields=[
                        "question_url",
                        "url_pending",
                        "updated_at",
                    ]
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(invalid)} URL(s) limpa(s) e marcada(s) como pendente(s)."
            )
        )
