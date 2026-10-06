# BillBot

A Telegram bot that reads Brazilian **boletos** (bank payment slips) and gives you back
just the part you actually need: the barcode.

Send Bill a photo or a PDF of a boleto. It downloads the file, extracts the barcode, due
date, value and issuer with OpenAI GPT-4o vision, saves the result to SQLite, and replies
with your full list of stored boletos so you can copy a barcode straight into your
banking app. All user-facing messages are in Portuguese.

## Features

- Accepts **photos** and **PDF documents** (every page of a multi-page PDF is processed).
- **GPT-4o vision extraction** of barcode (linha digitável), due date, value and issuer,
  with a self-reported confidence score.
- **Deduplication** — the barcode column is unique, so re-sending the same boleto is
  silently ignored instead of creating a second row.
- **Per-user history** — boletos are keyed to the sending Telegram user.
- **Async queue with pluggable consumers** — the bot acks immediately and processes in the
  background; new processing steps are added by registering another consumer.
- **Normalized storage** — values are parsed to cents and due dates to `datetime`, while
  the original OCR strings are kept alongside them.

## Tech stack

- Python 3.13, managed with [uv](https://docs.astral.sh/uv/)
- [python-telegram-bot](https://python-telegram-bot.org/) 22 (polling mode and all Telegram API calls)
- FastAPI + Uvicorn (webhook mode)
- SQLAlchemy 2 async + aiosqlite
- Pydantic / pydantic-settings
- OpenAI SDK (`gpt-4o`)
- PyMuPDF for PDF → image rendering

## Requirements

- Python 3.13 (see `.python-version`)
- `uv`
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- An OpenAI API key with access to `gpt-4o`

## Setup

```bash
uv sync
```

Create a `.env` file in the repository root:

```env
TELEGRAM_BOT_TOKEN=123456:your-bot-token
OPENAI_API_KEY=sk-your-key

# optional
DATABASE_URL=sqlite+aiosqlite:///billbot.db
OPENAI_MODEL=gpt-4o
DEBUG=false
```

Both `.env` and `billbot.db` are gitignored.

## Running

```bash
uv run python -m app.polling
```

This is the primary way to run the bot. It initializes the database (creating
`billbot.db` and its tables on first run), wires the consumers, starts the queue
processor, and connects to Telegram in long-polling mode — no public URL or tunnel
needed. If `TELEGRAM_BOT_TOKEN` or `OPENAI_API_KEY` is missing the process logs an error
and exits with status 1.

Webhook mode runs the same pipeline behind FastAPI:

```bash
uv run uvicorn app.main:app
```

Telegram must be pointed at `POST /api/webhook/telegram` (via `setWebhook`); `/health`
returns `{"status": "healthy"}`.

## How it works

```
Telegram update (polling: app/bot/handlers.py · webhook: app/api/routes/webhook.py)
      │  to_queue_message                ──► immediate "🔄 Processando..." reply
      ▼
 MessageQueue (app/worker/queue.py)
      │  runs every consumer in order
      ├─► LoggingConsumer   — debug logging
      ├─► OcrConsumer       — download → (PDF→PNG) → GPT-4o → store
      └─► ResponseConsumer  — reply with the user's boleto list
                                      │
                             SQLite (users, boletos)
```

1. Both entrypoints build a single `Container` (`app/container.py`), the composition root
   that creates the database, OpenAI client, Telegram bot, services and queue, and wires
   them together through constructor injection. Nothing else reads settings or holds
   module-level state.
2. `/start`, file and catch-all handlers (`app/bot/handlers.py`) — or the webhook route —
   convert the Telegram message into a `QueueMessage` (`app/schemas/queue.py`) with
   `to_queue_message` (`app/bot/mapper.py`) and enqueue it. The user is acked right away.
3. `MessageQueue` drains the queue in a background task and runs each consumer in turn,
   logging and swallowing per-consumer exceptions so one failure doesn't drop the message.
4. `OcrConsumer` (`app/worker/consumers.py`) fetches the file through `TelegramGateway`
   (`app/bot/gateway.py`). PDFs go through `render_pdf_pages` (`app/services/pdf.py`,
   PyMuPDF at 200 DPI, one PNG per page, run off the event loop); images are used as-is.
5. Each image is sent to `BoletoExtractor` (`app/services/ocr.py`), which prompts
   `gpt-4o` for a JSON object and validates it into a `BoletoData`
   (`app/schemas/boleto.py`).
6. `BoletoService.store` (`app/services/boletos.py`) gets or creates the `User`, parses
   the value to cents and the due date to a `datetime` (`app/services/parsing.py`), and
   inserts a `Boleto` through the repositories in `app/repositories/`. A duplicate
   barcode raises `IntegrityError` and is logged and ignored.
7. `ResponseConsumer` replies with every stored boleto, newest first, formatted by
   `format_boleto_list` (`app/bot/messages.py`) as `*issuer - R$ value:*` followed by
   the barcode.

## Project layout

```
app/
├── container.py              # Composition root: builds and wires all dependencies
├── main.py                   # FastAPI app factory (webhook mode)
├── polling.py                # Polling entrypoint
├── api/
│   ├── dependencies.py       # Depends() providers backed by the container
│   └── routes/
│       └── webhook.py        # POST /api/webhook/telegram
├── bot/
│   ├── gateway.py            # TelegramGateway: file downloads, sending messages
│   ├── handlers.py           # python-telegram-bot handlers
│   ├── mapper.py             # Telegram Message → QueueMessage
│   └── messages.py           # All Portuguese user-facing text and formatters
├── core/
│   ├── config.py             # pydantic-settings Settings, loaded from .env
│   └── logging.py            # Logging setup
├── db/
│   ├── database.py           # Database: engine, sessions, table creation
│   └── models.py             # User, Boleto
├── repositories/
│   ├── boletos.py            # BoletoRepository
│   └── users.py              # UserRepository
├── schemas/
│   ├── boleto.py             # BoletoData (OCR contract), StoredBoleto
│   ├── queue.py              # QueueMessage + Chat/Message/User/FileInfo
│   └── telegram.py           # Raw webhook payload validation
├── services/
│   ├── boletos.py            # BoletoService: store and list boletos
│   ├── ocr.py                # BoletoExtractor: GPT-4o vision extraction
│   ├── parsing.py            # Currency and date parsing
│   └── pdf.py                # PDF → PNG via PyMuPDF
└── worker/
    ├── consumers.py          # Consumer protocol and pipeline consumers
    └── queue.py              # MessageQueue: in-process queue and processor
```

`docs/` holds the style guides this code follows — see [Conventions](#conventions).

## Data model

Two tables, created automatically by `Database.create_tables` (`app/db/database.py`):

- **`users`** — `telegram_id` (unique), `first_name`, `username`, `created_at`.
  Users are created lazily the first time they send a boleto.
- **`boletos`** — belongs to a user. Stores `barcode` (**unique**, the dedupe key),
  both parsed and raw forms of the due date (`due_date`, `due_date_raw`) and value
  (`value_cents`, `value_raw`), plus `issuer`, `confidence`, `raw_text`, `status`
  (defaults to `pending`) and `created_at` / `paid_at`.

The two unique constraints drive the behavior worth knowing about: one row per Telegram
user, and one row per barcode across the whole database. `status` and `paid_at` exist for
a future payment-tracking flow and are not written by any code path yet.

## Bot behavior

| Input | Result |
|---|---|
| `/start` | Personalized greeting from "Bill" explaining what to send |
| Photo | Queued, OCR'd, stored, then the full boleto list is sent back |
| Document (incl. PDF) | Same, with every PDF page processed separately |
| Anything else | Falls back to the `/start` greeting |

Failures are reported in Portuguese: an undownloadable file, an unreadable PDF, or a PDF
with no pages each get their own message asking the user to try again.

## Status and known issues

- **The queue is in-process and non-durable** — anything still pending is lost on restart,
  and processing does not scale beyond a single instance.
- **No tests and no linter configuration** yet.

## Conventions

The code follows the guides checked into `docs/`:

- `docs/python_best_practices.md` — Google Python style: Google-format docstrings on
  every public function, type annotations throughout, explicit imports.
- `docs/fastapi_best_practices.md` — the `api` / `core` / `schemas` / `services` /
  `db` layering this project uses (plus `repositories`, `bot` and `worker`), with
  business logic kept in `services/`, Pydantic models kept in `schemas/`, and
  dependencies injected rather than imported as globals.
