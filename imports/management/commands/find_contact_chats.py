from __future__ import annotations

from django.core.management.base import BaseCommand

from imports.services.contact_lookup import find_contact_chat_interactions


class Command(BaseCommand):
    help = "Lista chats/grupos em que um contato interagiu."

    def add_arguments(self, parser):
        parser.add_argument("contact", type=str, help="Nome (ou parte do nome) do contato")

    def handle(self, *args, **options):
        contact = options["contact"]
        interactions = find_contact_chat_interactions(contact)
        if not interactions:
            self.stdout.write(self.style.WARNING("Nenhuma interacao encontrada para o contato informado."))
            return

        self.stdout.write(self.style.SUCCESS(f"Interacoes para '{contact}':"))
        for item in interactions:
            self.stdout.write(
                f"- {item.participant_name} em '{item.chat_title}' ({item.messages_count} mensagens)"
            )
