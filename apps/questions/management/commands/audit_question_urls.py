from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.competitions.models import Competition
from apps.questions.models import QuestionRecord, is_supported_question_url


class Command(BaseCommand):
    help = (
        "Audita URLs das questões. A única URL aceita é a página individual "
        "da questão no Gran Questões. Com --fix, remove links de outras fontes "
        "e marca todo registro sem URL Gran como pendente."
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
                "Normaliza as URLs: mantém somente Gran individual, limpa as demais "
                "e marca registros sem URL Gran como pendentes."
            ),
        )

    def handle(self, *args, **options):
        queryset = QuestionRecord.objects.select_related(
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
        valid = [
            record
            for record in records
            if is_supported_question_url(record.question_url)
        ]
        non_gran_filled = [
            record
            for record in records
            if record.question_url
            and not is_supported_question_url(record.question_url)
        ]
        missing = [
            record
            for record in records
            if not is_supported_question_url(record.question_url)
        ]
        stale_pending = [
            record
            for record in valid
            if record.url_pending
        ]

        self.stdout.write(
            f"Questões auditadas: {len(records)} | "
            f"URLs Gran individuais: {len(valid)} | "
            f"links preenchidos que serão removidos: {len(non_gran_filled)} | "
            f"sem URL Gran: {len(missing)}"
        )

        for record in non_gran_filled[:25]:
            self.stdout.write(
                f"- {record.code} | "
                f"{record.competition_discipline.discipline.name} | "
                f"{record.question_url}"
            )

        if len(non_gran_filled) > 25:
            self.stdout.write(
                f"... e mais {len(non_gran_filled) - 25} link(s) a remover."
            )

        if not options["fix"]:
            self.stdout.write(
                "Auditoria concluída sem alterações. Use --fix para normalizar."
            )
            return

        with transaction.atomic():
            for record in records:
                valid_gran = is_supported_question_url(record.question_url)
                if valid_gran:
                    if record.url_pending:
                        record.url_pending = False
                        record.save(
                            update_fields=["url_pending", "updated_at"]
                        )
                    continue

                fields = []
                if record.question_url:
                    record.question_url = ""
                    fields.append("question_url")
                if not record.url_pending:
                    record.url_pending = True
                    fields.append("url_pending")
                if fields:
                    fields.append("updated_at")
                    record.save(update_fields=fields)

        self.stdout.write(
            self.style.SUCCESS(
                f"Normalização concluída: {len(non_gran_filled)} link(s) removido(s), "
                f"{len(missing)} questão(ões) sem Gran marcada(s) como pendente(s), "
                f"{len(stale_pending)} pendência(s) antiga(s) limpa(s) em URLs Gran válidas."
            )
        )
