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
- [python-telegram-bot](https://python-telegram-bot.org/) 22 (polling mode)
- FastAPI + Uvicorn (webhook mode — see [Status](#status-and-known-issues))
- SQLAlchemy 2 async + aiosqlite
- Pydantic / pydantic-settings
- OpenAI SDK (`gpt-4o`)
- PyMuPDF for PDF → image rendering
- httpx for direct Telegram API calls

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
DEBUG=false
```

Both `.env` and `billbot.db` are gitignored.

## Running

```bash
uv run python -m app.polling
```

This is the supported way to run the bot. It initializes the database (creating
`billbot.db` and its tables on first run), registers the consumers, starts the queue
processor, and connects to Telegram in long-polling mode — no public URL or tunnel
needed. If `TELEGRAM_BOT_TOKEN` is missing the process logs an error and exits with
status 1.

## How it works

```
Telegram message
      │
      ▼
 handler (app/polling.py)          ──► immediate "🔄 Processando..." reply
      │  create_queue_message
      ▼
 asyncio.Queue (app/services/queue.py)
      │  process_queue runs every registered consumer in order
      ├─► logger_consumer      — debug logging
      ├─► ocr_consumer         — download → (PDF→PNG) → GPT-4o → store
      └─► response_consumer    — reply with the user's boleto list
                                      │
                             SQLite (users, boletos)
```

1. `/start`, document, photo and catch-all handlers in `app/polling.py` receive updates.
2. `create_queue_message` (`app/services/queue.py`) normalizes the Telegram message into a
   `QueueMessage` (`app/schemas/queue.py`) and `enqueue` puts it on an in-process
   `asyncio.Queue`. The user is acked right away.
3. `process_queue` drains the queue and runs each registered consumer in turn, logging and
   swallowing per-consumer exceptions so one failure doesn't drop the message.
4. `ocr_consumer` (`app/services/consumers.py`) fetches the file via the Telegram file API.
   PDFs go through `convert_pdf_to_images` (`app/services/pdf_service.py`, PyMuPDF at
   200 DPI, one PNG per page); images are used as-is.
5. Each image is sent to `extract_boleto_data` (`app/services/ocr_service.py`), which
   prompts `gpt-4o` for a JSON object and validates it into a `BoletoData`
   (`app/schemas/ocr.py`).
6. `store_boleto` (`app/services/storage.py`) gets or creates the `User`, parses the value
   to cents and the due date to a `datetime`, and inserts a `Boleto`. A duplicate barcode
   raises `IntegrityError` and is logged and ignored.
7. `response_consumer` replies via `get_user_boletos_response`
   (`app/services/message_handler.py`) with every stored boleto, newest first, formatted
   as `*issuer - R$ value:*` followed by the barcode.

## Project layout

```
app/
├── main.py                   # FastAPI app: lifespan init_db, /health, /api router
├── polling.py                # Polling entrypoint — the supported way to run the bot
├── api/
│   ├── dependencies.py       # (empty placeholder)
│   └── routes/
│       └── webhook.py        # POST /api/webhook/telegram (see Status)
├── core/
│   └── config.py             # pydantic-settings Settings, loaded from .env
├── db/
│   ├── models.py             # User, Boleto
│   └── session.py            # async engine, sessionmaker, init_db
├── schemas/
│   ├── ocr.py                # BoletoData — the OCR contract
│   ├── queue.py              # QueueMessage + Chat/Message/User/FileInfo
│   └── telegram.py           # Raw webhook payload validation
└── services/
    ├── command_handler.py    # /start greeting template
    ├── consumers.py          # logger_consumer, ocr_consumer, download/send helpers
    ├── message_handler.py    # Boleto list formatting
    ├── ocr_service.py        # GPT-4o vision extraction
    ├── pdf_service.py        # PDF → PNG via PyMuPDF
    ├── queue.py              # In-process queue, consumer registry, processor
    └── storage.py            # Users/boletos persistence and value/date parsing
```

`agent_docs/` holds the style guides this code follows — see [Conventions](#conventions).

## Data model

Two tables, created automatically by `init_db` (`app/db/session.py`):

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

- **Webhook mode is broken.** `app/api/routes/webhook.py:10` imports `process_document`
  and `process_photo` from `app.services.message_handler`, which no longer defines them,
  so `import app.main` raises `ImportError` and neither `uv run uvicorn app.main:app` nor
  `/health` nor `POST /api/webhook/telegram` can start. Use polling mode. Reviving the
  webhook also means routing it through the queue, which it currently bypasses.
- **The queue is in-process and non-durable** — anything still pending is lost on restart,
  and processing does not scale beyond a single instance.
- **Unused code**: `format_boleto_response` (`app/services/ocr_service.py`) and
  `get_queue_size` (`app/services/queue.py`); `app/api/dependencies.py` is an empty stub.
- **No tests and no linter configuration** yet.

## Conventions

The code follows the guides checked into `agent_docs/`:

- `agent_docs/python_best_practices.md` — Google Python style: Google-format docstrings on
  every public function, type annotations throughout, explicit imports.
- `agent_docs/fastapi_best_practices.md` — the `api` / `core` / `schemas` / `services` /
  `db` layering this project uses, with business logic kept in `services/` and Pydantic
  models kept in `schemas/`.
