from __future__ import annotations

import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from imports.services.ingest_zip import ingest_whatsapp_zip


class Command(BaseCommand):
    help = "Importa um ZIP exportado do WhatsApp (txt + midia)."

    def add_arguments(self, parser):
        parser.add_argument("zip_path", type=str, help="Caminho para o arquivo ZIP exportado")
        parser.add_argument("--timezone", default="America/Fortaleza", help="Timezone de parsing")
        parser.add_argument("--chat-name", default=None, help="Nome de chat para override")
        parser.add_argument("--dry-run", action="store_true", help="Apenas parseia sem persistir")

    def handle(self, *args, **options):
        zip_path = options["zip_path"]
        if not Path(zip_path).exists():
            raise CommandError(f"Arquivo nao encontrado: {zip_path}")

        output_encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        safe_zip_path = zip_path.encode(output_encoding, errors="replace").decode(output_encoding)
        self.stdout.write(self.style.WARNING(f"Iniciando importacao de: {safe_zip_path}"))
        summary = ingest_whatsapp_zip(
            zip_path,
            timezone_name=options["timezone"],
            chat_name=options["chat_name"],
            dry_run=options["dry_run"],
        )

        mode = "DRY-RUN" if options["dry_run"] else "IMPORTACAO"
        self.stdout.write(self.style.SUCCESS(f"{mode} finalizada com sucesso"))
        self.stdout.write(
            "\n".join(
                [
                    f"- mensagens importadas: {summary.imported_messages}",
                    f"- mensagens duplicadas ignoradas: {summary.duplicated_messages}",
                    f"- participantes: {summary.participants_total}",
                    f"- refs de midia encontradas: {summary.media_refs_found}",
                    f"- refs de midia faltantes: {summary.missing_media_refs}",
                    f"- midias extraidas: {summary.extracted_media}",
                    f"- midias deduplicadas: {summary.deduplicated_media}",
                ]
            )
        )
