# ZapIA (Django 6.0.4)

Importador de exportacoes do WhatsApp (`.zip` com `.txt` + midia) para banco SQLite, com service layer dedicada e comportamento idempotente.

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

Inicializacao Django (ja executada neste repositório):

```bash
django-admin startproject zapia .
python manage.py startapp imports
```

Banco e testes:

```bash
python manage.py migrate
pytest
```

## Como usar

Comando principal:

```bash
python manage.py import_whatsapp_zip /caminho/arquivo.zip --timezone America/Fortaleza --chat-name "Grupo X"
```

Dry-run (nao persiste nada):

```bash
python manage.py import_whatsapp_zip /caminho/arquivo.zip --dry-run
```

## Arquitetura

- `imports/domain/types.py`: dataclasses e tipos do dominio intermediario (sem ORM).
- `imports/domain/parsing.py`: parser puro para texto de export do WhatsApp.
- `imports/services/ingest_zip.py`: orquestracao unzip + parse + persistencia em `transaction.atomic`.
- `imports/management/commands/import_whatsapp_zip.py`: CLI fina delegando para service layer.
- `imports/models.py`: modelo relacional para jobs, chats, participantes, mensagens e midias.

## Parsing suportado

- Selecao do `.txt` no ZIP priorizando `_chat.txt`, depois nomes tipo `WhatsApp Chat with ...`.
- Mensagens multiline: linhas sem cabecalho de data/hora sao anexadas a mensagem anterior.
- Mensagens de sistema: linhas sem prefixo `Sender:`.
- Referencias de midia:
  - `<attached: ARQUIVO.ext>`
  - `<Media omitted>`
- Datas/horas aceitas:
  - `DD/MM/YY`
  - `MM/DD/YY`
  - `DD.MM.YYYY`
  - horario 24h e 12h (`AM/PM`)

### Heuristica de ambiguidade de data

Por padrao, o parser usa preferencia `pt-BR` (`dayfirst=True`), priorizando `DD/MM` em datas ambiguas.

## Estrategia de idempotencia

- `ImportJob.sha256_zip` com `UNIQUE`: impede reprocessamento integral do mesmo ZIP.
- `MediaAsset.sha256` com `UNIQUE`: deduplica binarios de midia, inclusive entre import jobs diferentes.
- `Message` usa `content_hash` estavel com base em:
  - timestamp (ISO)
  - sender normalizado
  - texto normalizado
  - referencias de midia
- Constraint unica em `Message(chat, participant, timestamp, content_hash)`: evita duplicacao por mensagem.

### Limitacoes conhecidas

- Mudancas pequenas no texto original (ex.: espacos diferentes) podem alterar hash dependendo da normalizacao.
- Diferencas de timezone na origem do export podem impactar igualdade de timestamp.
- Associacao `MediaAsset -> Message` usa melhor esforco por nome de arquivo referenciado.

## Persistencia de midia

- Midia persistida diretamente no banco em `imports_mediaasset.payload` (`BinaryField`).
- Se houver referencias no texto, prioriza processar os arquivos referenciados.
- Se nao houver referencias, processa os anexos do ZIP e registra no banco.
- MIME e detectado por `mimetypes` (stdlib), com fallback para `application/octet-stream`.

## Banco de dados e evolucao

- Default: SQLite (`db.sqlite3`) para desenvolvimento inicial.
- Modelagem usa constraints/indexes portaveis e pode migrar para PostgreSQL sem alterar dominio/parser.

## Extras sugeridos (nao instalados)

- `psycopg[binary]` para PostgreSQL
- `Pillow` para enriquecer metadados de imagem
