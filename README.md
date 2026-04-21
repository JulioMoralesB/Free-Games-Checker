# Free Games Notifier

A Python-based scheduler that monitors the Epic Games Store for free game promotions and sends Discord notifications. Runs as a Docker container with health check support, optional PostgreSQL integration, a REST API, and a built-in web dashboard.

## Features

- ✅ **Daily Monitoring**: Automatically checks Epic Games Store at a configurable time (default: 12:00 UTC) for new free games
- 💬 **Discord Notifications**: Sends beautifully formatted Discord embeds with game details
- 📊 **Persistent Storage**: Maintains game history — PostgreSQL when `DB_HOST` is set, JSON file otherwise
- 🏥 **Health Checks**: Optional UptimeKuma/Healthchecks.io integration for monitoring
- 🌐 **Web Dashboard**: Browse and search the full history of tracked free games at `/dashboard/`
- 🔌 **REST API**: Built-in FastAPI endpoints for health, history, metrics, and notification management
- 🐳 **Docker Ready**: Includes Docker and docker-compose configurations
- 🌍 **Fully Configurable**: Timezone, locale, region, schedule time, and health check interval are all configurable via environment variables

## Prerequisites

### Local Development
- Python 3.9+
- pip (Python package manager)
- Virtual environment support (venv)
- Node.js 20+ and npm (only required to build the dashboard locally)

### Docker Deployment
- Docker 20.10+
- Docker Compose 1.29+
- (Optional) PostgreSQL 13+ for database-backed storage

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/JulioMoralesB/free-games-notifier.git
cd free-games-notifier
```

### 2. Create a Virtual Environment

```bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory (see [Environment Variables Reference](#environment-variables-reference) for all options):

```env
# Required
DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN

# Optional: PostgreSQL (file-based JSON by default)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=free_games
DB_USER=postgres
DB_PASSWORD=your_password

# Optional: Timezone / locale / region
TIMEZONE=UTC
LOCALE=en_US.UTF-8
EPIC_GAMES_REGION=en-US

# Optional: Scheduler
SCHEDULE_TIME=12:00
```

> To get your Discord webhook URL, go to **Server Settings → Integrations → Webhooks** and create a new webhook for the desired channel.

### 5. Run the Scheduler

```bash
python main.py
```

The service checks for new free games daily at `SCHEDULE_TIME` and logs activity to `/mnt/logs/notifier.log`.
In Docker deployments, this log path is typically backed by a bind-mounted host directory so logs persist outside the container.

## Storage Backends

The notifier automatically selects a storage backend based on the `DB_HOST` environment variable:

| `DB_HOST` set? | Backend used | Data location |
|---|---|---|
| ✅ Yes | PostgreSQL (`free_games` schema) | Remote database |
| ❌ No (default) | JSON file | `/mnt/data/free_games.json` |

> The application stores JSON-backed data under `/mnt/data/free_games.json`. In Docker deployments, `/mnt/data` is typically the container path you bind-mount to a host directory or volume for persistence.
When `DB_HOST` is configured the application creates the schema and applies any pending Alembic migrations automatically on startup. The database derives `game_id` from the game `link` and uses `ON CONFLICT (game_id) DO UPDATE` to upsert existing rows, refreshing fields such as `promotion_end_date`.

## Database Migrations

Schema changes are managed by [Alembic](https://alembic.sqlalchemy.org/) and applied **automatically on startup**. Migration scripts live in `alembic/versions/`.

| Revision | Description |
|----------|-------------|
| `0001`   | Initial schema — creates the `free_games` schema and `games` table |
| `0002`   | Widens `games.game_id` from `VARCHAR(255)` to `TEXT` |
| `0003`   | Converts `games.promotion_end_date` from `TIMESTAMP` to `TEXT` (ISO-8601 UTC) |
| `0004`   | Adds `last_notification` table for Discord resend support |

For manual migration commands and instructions for creating new migrations, see [docs/database-migrations.md](docs/database-migrations.md).

## REST API

The service exposes a FastAPI REST API on `API_HOST:API_PORT` (default `0.0.0.0:8000`). Interactive docs are available at `/docs`.

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/health` | GET | — | Epic Games API and database health check |
| `/games/latest` | GET | — | Most recently fetched free games |
| `/games/history` | GET | — | Paginated full game history (`limit`, `offset` query params) |
| `/notify/discord/resend` | POST | API key | Re-send last Discord notification |
| `/metrics` | GET | — | Uptime, games processed, notification counts |
| `/config` | GET | API key | Non-secret runtime configuration |
| `/check` | POST | API key | Full end-to-end pipeline test |
| `/dashboard/` | GET | — | Web dashboard (served as static files) |

Protected endpoints (`POST` methods and `GET /config`) require an `X-API-Key` header when `API_KEY` is set.

| Variable | Default | Description |
|---|---|---|
| `API_HOST` | `0.0.0.0` | Interface to bind the API server |
| `API_PORT` | `8000` | Port to listen on |
| `API_KEY` | _(empty)_ | Secret key for mutating endpoints and `GET /config`; leave empty to disable auth |

## Web Dashboard

The dashboard is a React/TypeScript SPA served at **`http://<host>:<API_PORT>/dashboard/`** — no additional container or CORS configuration needed.

![Web Dashboard](https://github.com/user-attachments/assets/1ffef230-45e2-4ef1-9ffb-6a7a9d573d62)

- Game cards with thumbnail, title, description, promotion end date, and Epic Games Store link
- Live search by title or description
- Sort by date or title
- Server-side pagination with smart ellipsis
- Responsive dark theme, no external UI framework
- English and Spanish built-in; browser language auto-detected; preference persisted in `localStorage`

For development setup, hot-reload, and adding new languages, see [docs/dashboard.md](docs/dashboard.md).

## Docker Deployment

### Quick Start

```bash
docker-compose up -d
```

### Using Only Docker

```bash
docker build -t free-games-notifier .
docker run -d \
  --name free-games-notifier \
  -e DISCORD_WEBHOOK_URL="YOUR_WEBHOOK_URL" \
  -e TIMEZONE=UTC \
  -e SCHEDULE_TIME=12:00 \
  free-games-notifier
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | ✅ Yes | - | Discord webhook URL for sending notifications |
| `EPIC_GAMES_API_URL` | ❌ No | Official API | Epic Games Store API endpoint |
| `ENABLED_STORES` | ❌ No | `epic` | Comma-separated list of stores to scrape. Supported: `epic`, `steam` (e.g. `epic,steam`) |
| `STEAM_REQUEST_DELAY_MS` | ❌ No | `1500` | Milliseconds to wait between Steam HTTP requests to avoid rate limiting |
| `HEALTHCHECK_URL` | ❌ No | - | Healthchecks.io or UptimeKuma ping URL |
| `ENABLE_HEALTHCHECK` | ❌ No | `false` | Enable health check pings (`true`/`false`) |
| `DB_HOST` | ❌ No | - | PostgreSQL host (leave empty to use file storage) |
| `DB_PORT` | ❌ No | `5432` | PostgreSQL port |
| `DB_NAME` | ❌ No | - | PostgreSQL database name |
| `DB_USER` | ❌ No | - | PostgreSQL username |
| `DB_PASSWORD` | ❌ No | - | PostgreSQL password |
| `TIMEZONE` | ❌ No | `UTC` | IANA timezone name (e.g. `America/New_York`, `Europe/London`) |
| `LOCALE` | ❌ No | `en_US.UTF-8` | Locale for date formatting (e.g. `es_ES.UTF-8`, `de_DE.UTF-8`) |
| `EPIC_GAMES_REGION` | ❌ No | `en-US` | Region code for Epic Games Store links (e.g. `es-MX`, `de-DE`) |
| `SCHEDULE_TIME` | ❌ No | `12:00` | Daily check time in `HH:MM`, interpreted in `TIMEZONE` |
| `HEALTHCHECK_INTERVAL` | ❌ No | `1` | Health check ping interval in minutes |
| `DATE_FORMAT` | ❌ No | `%B %d, %Y at %I:%M %p` | strftime format for the promotion end date in Discord notifications |
| `API_HOST` | ❌ No | `0.0.0.0` | Interface the REST API and dashboard server binds to |
| `API_PORT` | ❌ No | `8000` | Port the REST API and dashboard server listens on |
| `API_KEY` | ❌ No | _(empty)_ | Secret key for mutating API endpoints; leave empty to disable auth |

### Steam notes

- Free game promotions on Steam are infrequent. When only Steam is enabled (or when Steam returns no results), the scheduler will log "No free games found" more often than with Epic — this is expected.
- Steam requests are throttled by `STEAM_REQUEST_DELAY_MS` (default 1 500 ms) to avoid hitting rate limits. Lowering this value may cause HTTP 429 errors; raising it is safe.

## Project Structure

```
.
├── main.py                 # Main scheduler entry point
├── api.py                  # FastAPI REST API + dashboard static file mount
├── config.py               # Configuration and environment variables
├── requirements.txt        # Python dependencies
├── alembic.ini             # Alembic migration tool configuration
├── Dockerfile              # Multi-stage Docker image (Node.js builder + Python runtime)
├── compose.yaml            # Docker Compose orchestration
├── dashboard/              # React/TypeScript web dashboard (Vite)
├── alembic/versions/       # Versioned migration scripts
├── modules/
│   ├── scrapers/           # Store scraper implementations (Epic, Steam, …)
│   ├── notifier.py         # Discord webhook sender
│   ├── storage.py          # Storage dispatcher (PostgreSQL or JSON file)
│   ├── database.py         # PostgreSQL database operations
│   ├── models.py           # Shared FreeGame dataclass
│   └── healthcheck.py      # Health check monitoring
└── data/
    ├── free_games.json     # Local game history (file-based storage only)
    └── logs/               # Application logs
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Tests cover both the file-backend and PostgreSQL-backend paths. File-backend tests explicitly set `DB_HOST=None` to remain hermetic.

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md) for common issues and solutions.

Logs are written to `/mnt/logs/notifier.log` and rotated weekly:

```bash
tail -f /mnt/logs/notifier.log
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

- 🐛 [Report Issues](https://github.com/JulioMoralesB/Free-Games-Notifier/issues)

## Roadmap

- [x] Unit test coverage (#9)
- [x] PostgreSQL as primary storage (#11)
- [x] Configurable timezone and region (#12)
- [x] Retry logic with exponential backoff (#13)
- [x] Dockerfile security and modernization (#14)
- [x] Database migrations with Alembic (#26)
- [x] REST API for health, history, metrics, and notification management (#29)
- [x] Web dashboard for game history (#46)
- [x] Production end-to-end test suite (#49)
- [ ] Add support for multiple notification channels (Discord, Slack, Telegram, etc.) (#55)
- [ ] UI/UX Enhancements (#71)
- [x] Support for additional game stores — Steam (#56)

