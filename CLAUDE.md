# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Telegram bot that tracks message statistics in group chats. Uses polling (not webhooks). One bot instance can serve multiple groups simultaneously — all queries are scoped by `chat_id`.

## Running locally

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## Docker

```bash
# Build and run
docker compose up --build

# Run in background
docker compose up -d
```

## Architecture

Single-file bot (`bot.py`):
- `init_db()` — creates SQLite table on startup via `post_init` hook
- `track_message()` — handler for all non-command text messages; inserts a row per message
- `stats()` — handler for `/stats`; queries last 24h grouped by `user_id`, scoped to `chat_id`

Storage: SQLite file (`stats.db`) with a single `messages` table. In Docker, the DB is stored in `/app/data/` (mounted as a volume).

## Environment

Requires `.env` file with:
```
BOT_TOKEN=<telegram bot token>
```

Bot must have Privacy Mode disabled in BotFather to receive non-command messages in groups.
