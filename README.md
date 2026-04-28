# WhatsApp ZIP Ingestor (Django)

Projeto Django para importar exportacoes de chat do WhatsApp (ZIP com `_chat.txt` e midia) para SQLite, com estrategia idempotente para evitar duplicacao em reimportacoes.

## Setup local

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Depois:

```bash
django-admin startproject whatsapp_ingestor .
python manage.py startapp imports
```

## Tooling

- `pytest` + `pytest-django` para testes
- `ruff` para lint

## Extras sugeridos (nao instalados por padrao)

- `psycopg[binary]` para PostgreSQL
- `Pillow` para processamento de imagem
