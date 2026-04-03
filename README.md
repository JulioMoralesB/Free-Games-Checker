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

Create a `.env` file in the root directory:

```env
# Required: Discord webhook for notifications
DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN

# Optional: Epic Games API (defaults to official store API)
EPIC_GAMES_API_URL=https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions

# Optional: Health Check Monitoring
HEALTHCHECK_URL=https://healthchecks.io/ping/YOUR_UUID
ENABLE_HEALTHCHECK=false

# Optional: PostgreSQL Database (file-based JSON by default)
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
HEALTHCHECK_INTERVAL=1
```

### 5. Run the Scheduler

```bash
python main.py
```

The service will:
- Check for new free games daily at the configured `SCHEDULE_TIME` (default: 12:00 in the configured `TIMEZONE`)
- Send health check pings every `HEALTHCHECK_INTERVAL` minutes (if enabled)
- Log activity to `data/logs/notifier.log`

## Storage Backends

The notifier automatically selects a storage backend based on the `DB_HOST` environment variable:

| `DB_HOST` set? | Backend used | Data location |
|---|---|---|
| ✅ Yes | PostgreSQL (`free_games` schema) | Remote database |
| ❌ No (default) | JSON file | `data/free_games.json` |

### PostgreSQL backend

When `DB_HOST` is configured the application will:

1. Create the `free_games` schema and the `games` table on first startup (idempotent)
2. Apply any pending Alembic migrations automatically on startup (see [Database Migrations](#database-migrations) below)
3. Use `link` as the stable deduplication key (`ON CONFLICT DO NOTHING`)

If all `DB_*` variables are left unset the service falls back to the JSON file backend with no code or configuration changes required.

## Database Migrations

When using the PostgreSQL backend, Alembic migrations are applied automatically on startup to keep the database schema up to date.
## REST API

The service exposes a FastAPI REST API on `API_HOST:API_PORT` (default `0.0.0.0:8000`). The auto-generated interactive docs are available at `/docs`.

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/health` | GET | — | Epic Games API and database health check |
| `/games/latest` | GET | — | Most recently fetched free games |
| `/games/history` | GET | — | Paginated full game history (`limit`, `offset` query params) |
| `/notify/discord/resend` | POST | API key | Re-send last Discord notification |
| `/metrics` | GET | — | Uptime, games processed, notification counts |
| `/config` | GET | — | Non-secret runtime configuration |
| `/check` | POST | API key | Full end-to-end pipeline test |
| `/dashboard/` | GET | — | Web dashboard (served as static files) |

### Authentication

Protected endpoints (`POST`) require an `X-API-Key` header when `API_KEY` is set. Read-only (`GET`) endpoints are always public.

### REST API environment variables

| Variable | Default | Description |
|---|---|---|
| `API_HOST` | `0.0.0.0` | Interface to bind the API server |
| `API_PORT` | `8000` | Port to listen on |
| `API_KEY` | _(empty)_ | Secret key for mutating endpoints; leave empty to disable auth |

## Web Dashboard

The dashboard is a React/TypeScript SPA served by the same FastAPI process at **`http://<host>:<API_PORT>/dashboard/`** — no additional container, port, or CORS configuration needed.

![Web Dashboard](https://github.com/user-attachments/assets/1ffef230-45e2-4ef1-9ffb-6a7a9d573d62)

### Features

- **Game cards** — thumbnail with fallback, title, description, promotion end date, store badge, and a direct Epic Games Store link
- **Search** — live filter by title or description
- **Sort** — by date (newest/oldest) or title (A-Z / Z-A) with one-click direction toggle
- **Pagination** — server-side pagination using the `/games/history` API; smart ellipsis for large datasets
- **Responsive layout** — single column on mobile, two columns on tablet, auto-fill grid on desktop
- **Dark theme** — gaming-themed dark UI with CSS custom properties; no external UI framework
- **Multi-language (i18n)** — English and Spanish built-in; browser language is auto-detected; user preference is persisted in `localStorage`

### Language Support (i18n)

The dashboard auto-detects the visitor's preferred language from `navigator.languages` and falls back to English if the browser language is not supported. A language selector in the header lets the user manually switch between available languages; the choice is remembered across sessions via `localStorage`.

#### Adding a new language

All translation strings live in one file: **`dashboard/src/i18n/translations.ts`**.

1. **Add your locale code** to the `Locale` union type:
   ```ts
   export type Locale = 'en' | 'es' | 'fr'   // ← add 'fr' (French)
   ```
2. **Create a translation object** that implements the `Translations` interface:
   ```ts
   const fr: Translations = {
     headerTitle: 'Historique des jeux gratuits',
     headerSubtitle: 'Toutes les promotions de jeux gratuits suivies',
     gamesTracked: (count) => `${count} jeux suivis`,
     // … fill in all remaining keys …
   }
   ```
3. **Register it** in the `translations` map and add its BCP 47 language tag:
   ```ts
   export const translations: Record<Locale, Translations> = { en, es, fr }

   export const localeBcp47: Record<Locale, string> = {
     en: 'en-US',
     es: 'es-ES',
     fr: 'fr-FR',
   }
   ```
4. **Add a flag/label** in `dashboard/src/components/LanguageSelector.tsx`:
   ```ts
   const LOCALE_LABELS: Record<Locale, string> = {
     en: '🇺🇸 EN',
     es: '🇲🇽 ES',
     fr: '🇫🇷 FR',
   }
   ```
5. Rebuild the dashboard (`npm run build`) — no other changes required.

TypeScript will enforce that all keys of `Translations` are present; the compiler will report missing strings if you leave any out.

### Building the dashboard locally

The dashboard source lives in `dashboard/`. When deploying via Docker the Dockerfile builds it automatically in a multi-stage build (Node.js builder → Python runtime). To build it manually for local development:

```bash
cd dashboard
npm install
npm run build   # output goes to dashboard/dist/
```

Then start the Python service normally — FastAPI will detect and serve `dashboard/dist/`.

### Dashboard development (hot-reload)

```bash
# Terminal 1 — start the Python API
python main.py

# Terminal 2 — start the Vite dev server (proxies /games → localhost:8000)
cd dashboard
npm install
npm run dev     # http://localhost:5173/dashboard/
```



Schema changes are managed by [Alembic](https://alembic.sqlalchemy.org/). Versioned migration scripts live in `alembic/versions/`.

### Current migrations

| Revision | Description |
|----------|-------------|
| `0001`   | Initial schema — creates the `free_games` schema and `games` table |
| `0002`   | Widens `games.game_id` from `VARCHAR(255)` to `TEXT` |
| `0003`   | Converts `games.promotion_end_date` from `TIMESTAMP` to `TEXT` (ISO-8601 UTC) |

### Running migrations

Ensure your DB environment variables are set (see [Configure Environment Variables](#4-configure-environment-variables)), then run:

```bash
# Apply all pending migrations (safe to run on first-time or existing deployments)
alembic upgrade head

# Show current revision
alembic current

# Show migration history
alembic history --verbose

# Roll back one revision
alembic downgrade -1
```

On **Docker / docker-compose** deployments the application applies migrations automatically at startup via `alembic upgrade head`. You can also run them manually inside the container:

```bash
docker exec free-games-notifier alembic upgrade head
```

> **Note for existing deployments:** The migration scripts use conditional SQL so they are safe to run against databases created by the old `init_db()` logic — columns that are already the correct type are left unchanged.

### Creating a new migration

```bash
alembic revision -m "describe your change here"
# Edit the generated file in alembic/versions/ to add upgrade()/downgrade() logic
```

## Docker Deployment

### Quick Start with Docker Compose

```bash
docker-compose up -d
```

This will start:
- **free-games-notifier** service (runs scheduler)
- **PostgreSQL** database (optional, configure in compose.yaml)

### Using Only Docker

```bash
docker build -t free-games-notifier .
docker run -d \
  --name free-games-notifier \
  -e DISCORD_WEBHOOK_URL="YOUR_WEBHOOK_URL" \
  -e ENABLE_HEALTHCHECK=false \
  -e TIMEZONE=UTC \
  -e LOCALE=en_US.UTF-8 \
  -e EPIC_GAMES_REGION=en-US \
  -e SCHEDULE_TIME=12:00 \
  -e HEALTHCHECK_INTERVAL=1 \
  -v /mnt/data:/mnt/data \
  -v /mnt/logs:/mnt/logs \
  free-games-notifier
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | ✅ Yes | - | Discord webhook URL for sending notifications |
| `EPIC_GAMES_API_URL` | ❌ No | Official API | Epic Games Store API endpoint |
| `HEALTHCHECK_URL` | ❌ No | - | Healthchecks.io or UptimeKuma ping URL |
| `ENABLE_HEALTHCHECK` | ❌ No | `false` | Enable health check pings (`true`/`false`) |
| `DB_HOST` | ❌ No | - | PostgreSQL host (leave empty to use file storage) |
| `DB_PORT` | ❌ No | `5432` | PostgreSQL port |
| `DB_NAME` | ❌ No | - | PostgreSQL database name |
| `DB_USER` | ❌ No | - | PostgreSQL username |
| `DB_PASSWORD` | ❌ No | - | PostgreSQL password |
| `TIMEZONE` | ❌ No | `UTC` | IANA timezone name for date display and schedule interpretation (e.g. `America/New_York`, `Europe/London`) |
| `LOCALE` | ❌ No | `en_US.UTF-8` | Locale for date formatting (e.g. `es_ES.UTF-8`, `de_DE.UTF-8`). Must be available in the system. |
| `EPIC_GAMES_REGION` | ❌ No | `en-US` | Region code used in Epic Games Store links (e.g. `es-MX`, `de-DE`) |
| `SCHEDULE_TIME` | ❌ No | `12:00` | Daily check time in `HH:MM` format, interpreted in the configured `TIMEZONE` |
| `HEALTHCHECK_INTERVAL` | ❌ No | `1` | Health check ping interval in minutes |
| `DATE_FORMAT` | ❌ No | `%B %d, %Y at %I:%M %p` | strftime format for the promotion end date in Discord notifications |
| `API_HOST` | ❌ No | `0.0.0.0` | Interface the REST API and dashboard server binds to |
| `API_PORT` | ❌ No | `8000` | Port the REST API and dashboard server listens on |
| `API_KEY` | ❌ No | _(empty)_ | Secret key for mutating API endpoints; leave empty to disable auth |

## How to Get a Discord Webhook URL

1. Go to your Discord server → Server Settings → Channels & Roles
2. Select the channel where notifications should appear
3. Click "Edit Channel" → Integrations → Webhooks
4. Click "Create Webhook"
5. Copy the webhook URL and add to `.env`

## Project Structure

```
.
├── main.py                 # Main scheduler entry point
├── api.py                 # FastAPI REST API + dashboard static file mount
├── config.py              # Configuration and environment variables
├── requirements.txt       # Python dependencies
├── alembic.ini            # Alembic migration tool configuration
├── Dockerfile            # Multi-stage Docker image (Node.js builder + Python runtime)
├── compose.yaml          # Docker Compose orchestration
├── dashboard/             # React/TypeScript web dashboard (Vite)
│   ├── package.json      # Node.js dependencies
│   ├── vite.config.ts    # Vite config (base path /dashboard/, dev proxy)
│   ├── tsconfig.json     # TypeScript configuration
│   ├── index.html        # HTML entry point
│   └── src/
│       ├── main.tsx      # React entry point
│       ├── App.tsx        # Root component (search, sort, pagination)
│       ├── index.css      # Global responsive dark-theme styles
│       ├── types.ts       # TypeScript types (GameItem, API responses)
│       └── components/
│           ├── GameCard.tsx    # Individual game card component
│           └── Pagination.tsx  # Pagination with ellipsis
├── alembic/
│   ├── env.py            # Alembic runtime environment (reads config.py)
│   ├── script.py.mako    # Migration script template
│   └── versions/         # Versioned migration scripts
│       ├── 0001_initial_schema.py
│       ├── 0002_widen_game_id.py
│       └── 0003_promotion_end_date_to_text.py
├── modules/
│   ├── scrapper.py      # Epic Games API fetch logic
│   ├── notifier.py      # Discord webhook sender
│   ├── storage.py       # Storage dispatcher (PostgreSQL or JSON file)
│   ├── database.py      # PostgreSQL database operations
│   └── healthcheck.py   # Health check monitoring
├── data/
│   ├── free_games.json  # Local game history (file-based storage only)
│   └── logs/            # Application logs
└── README.md            # This file
```

## Logging

Logs are written to `data/logs/notifier.log` and rotated weekly. The log format includes:
- Timestamp
- Module name
- Log level (INFO, WARNING, ERROR, DEBUG)
- Message

View logs:
```bash
tail -f data/logs/notifier.log
```

## Troubleshooting

### Common Issues

#### 1. "Discord webhook URL not set!"
- **Problem**: Notifications fail silently
- **Solution**: Verify `DISCORD_WEBHOOK_URL` is set in `.env` and the webhook is valid
- **Check**: Run `grep DISCORD_WEBHOOK_URL .env` to confirm it's loaded

#### 2. AttributeError on missing environment variables
- **Problem**: Service crashes during startup
- **Solution**: Ensure all required variables are defined (at minimum: `DISCORD_WEBHOOK_URL`)
- **Check**: Run `printenv | grep DISCORD` to verify

#### 3. Database connection errors
- **Problem**: "psycopg2.OperationalError: could not connect to server"
- **Solution**: Verify PostgreSQL credentials in `.env` or disable database (`DB_HOST` commented out)
- **Check**: Test connection: `psql -h DB_HOST -U DB_USER -d DB_NAME`

#### 4. No logs appearing
- **Problem**: `data/logs/` directory doesn't exist
- **Solution**: Create logs directory: `mkdir -p data/logs`
- **Docker**: Mount volume: `-v $(pwd)/data/logs:/mnt/logs`

#### 5. Games not detected
- **Problem**: Service runs but no notifications sent
- **Solution**: 
  - Check if Epic Games API is responding (may be rate limited)
  - Verify Discord webhook is still valid (webhooks expire)
  - Check logs for parsing errors: `grep ERROR data/logs/notifier.log`

#### 6. Health check pings failing
- **Problem**: Healthchecks.io shows "Down"
- **Solution**: 
  - Verify `HEALTHCHECK_URL` is correct
  - Check if `ENABLE_HEALTHCHECK=true` is set
  - Ensure container has internet access

## Docker Troubleshooting

```bash
# View running container logs
docker logs free-games-notifier

# Execute command in container
docker exec free-games- cat /mnt/data/free_games.json

# Restart service
docker restart free-games-notifier

# Stop and remove
docker-compose down
```

## Contributing

Contributions are welcome! Please:

1. Open an issue to discuss major changes
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add feature description'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a pull request

## Testing

Run the test suite with:

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

The tests cover both the file-backend and PostgreSQL-backend paths in `storage.py`. File-backend tests explicitly set `DB_HOST=None` so they remain hermetic even when a database is available in the environment.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](README.md)
- 🐛 [Report Issues](https://github.com/JulioMoralesB/Free-Games-Notifier/issues)
- 💬 [Discussions](https://github.com/JulioMoralesB/Free-Games-Notifier/discussions)

## Roadmap

- [x] Unit test coverage (#9)
- [x] PostgreSQL as primary storage (#11)
- [x] Configurable timezone and region (#12)
- [x] Retry logic with exponential backoff (#13)
- [x] Dockerfile security and modernization (#14)
- [x] Database migrations with Alembic (#26)
- [x] REST API for health, history, metrics, and notification management (#29)
- [x] Web dashboard for game history (#46)
- [ ] Support for additional game stores (Steam, GOG, etc.)
- [ ] Production end-to-end test suite (#49)
