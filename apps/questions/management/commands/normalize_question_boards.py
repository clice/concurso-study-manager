from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.questions.models import QuestionRecord, normalize_board_name


class Command(BaseCommand):
    help = (
        "Audita e padroniza nomes de banca nas questões. "
        "Sem --fix, apenas mostra o diagnóstico."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Aplica a normalização no banco local.",
        )

    def handle(self, *args, **options):
        records = list(
            QuestionRecord.objects.exclude(board="")
            .only("id", "board")
            .order_by("id")
        )

        changes = []
        for record in records:
            canonical = normalize_board_name(record.board)
            if canonical != record.board:
                changes.append((record, canonical))

        grouped = Counter(
            (record.board, canonical)
            for record, canonical in changes
        )

        self.stdout.write(
            f"Questões com banca: {len(records)} | "
            f"registros a normalizar: {len(changes)} | "
            f"variações consolidadas: {len(grouped)}"
        )

        for (source, target), count in sorted(grouped.items()):
            self.stdout.write(f"- {source} -> {target}: {count}")

        if not options["fix"]:
            self.stdout.write(
                "Auditoria concluída sem alterações. Use --fix para aplicar."
            )
            return

        with transaction.atomic():
            for record, canonical in changes:
                record.board = canonical
                record.save(update_fields=["board", "updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(changes)} registro(s) de banca normalizado(s)."
            )
        )
