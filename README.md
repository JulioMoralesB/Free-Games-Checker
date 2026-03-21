# Free Games Notifier

A Python-based scheduler that monitors the Epic Games Store for free game promotions and sends Discord notifications. Runs as a Docker container with health check support and optional PostgreSQL integration.

## Features

- ✅ **Daily Monitoring**: Automatically checks Epic Games Store at 12:00 UTC for new free games
- 💬 **Discord Notifications**: Sends beautifully formatted Discord embeds with game details
- 📊 **Persistent Storage**: Maintains game history — PostgreSQL when `DB_HOST` is set, JSON file otherwise
- 🏥 **Health Checks**: Optional UptimeKuma/Healthchecks.io integration for monitoring
- 🐳 **Docker Ready**: Includes Docker and docker-compose configurations
- 🌍 **Timezone Support**: Automatically converts times to your timezone (currently Mexico City)

## Prerequisites

### Local Development
- Python 3.9+
- pip (Python package manager)
- Virtual environment support (venv)

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
```

### 5. Run the Scheduler

```bash
python main.py
```

The service will:
- Check for new free games daily at 12:00 UTC
- Send health check pings every minute (if enabled)
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
2. Automatically run `ALTER TABLE` migrations on existing deployments:
   - Widens `game_id` from `VARCHAR(255)` to `TEXT` (supports arbitrarily long Epic URLs)
   - Converts `promotion_end_date` from `TIMESTAMP` to `TEXT`, preserving the ISO-8601 format the scraper returns
3. Use `link` as the stable deduplication key (`ON CONFLICT DO NOTHING`)

If all `DB_*` variables are left unset the service falls back to the JSON file backend with no code or configuration changes required.

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
| `ENABLE_HEALTHCHECK` | ❌ No | `false` | Enable health check pings (true/false) |
| `DB_HOST` | ❌ No | - | PostgreSQL host (leave empty to use file storage) |
| `DB_PORT` | ❌ No | 5432 | PostgreSQL port |
| `DB_NAME` | ❌ No | - | PostgreSQL database name |
| `DB_USER` | ❌ No | - | PostgreSQL username |
| `DB_PASSWORD` | ❌ No | - | PostgreSQL password |

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
├── config.py              # Configuration and environment variables
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yaml   # Docker Compose orchestration
├── compose.yaml          # Alternative compose config
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

- [x] Unit test coverage (Task #4)
- [x] PostgreSQL as primary storage (Task #5)
- [ ] Configurable timezone and region (Task #6)
- [ ] Retry logic with backoff (Task #7)
- [ ] Support for additional game stores (Steam, GOG, etc.)
- [ ] Web dashboard for game history
