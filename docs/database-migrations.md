# Database Migrations

Schema changes are managed by [Alembic](https://alembic.sqlalchemy.org/). Migration scripts live in `alembic/versions/` and are applied **automatically on startup** when `DB_HOST` is set.

## Current migrations

| Revision | Description |
|----------|-------------|
| `0001`   | Initial schema — creates the `free_games` schema and `games` table |
| `0002`   | Widens `games.game_id` from `VARCHAR(255)` to `TEXT` |
| `0003`   | Converts `games.promotion_end_date` from `TIMESTAMP` to `TEXT` (ISO-8601 UTC) |
| `0004`   | Adds `last_notification` table for Discord resend support |

## Running migrations manually

Ensure your DB environment variables are set, then run:

```bash
# Apply all pending migrations
alembic upgrade head

# Show current revision
alembic current

# Show migration history
alembic history --verbose

# Verify a table exists
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -c "SELECT to_regclass('free_games.last_notification');"

# Roll back one revision
alembic downgrade -1
```

Inside a Docker container:

```bash
docker exec free-games-notifier alembic upgrade head
```

> **Note for existing deployments:** Migration scripts use conditional SQL and are safe to run against databases created by the old `init_db()` logic — columns already at the correct type are left unchanged.

## Creating a new migration

```bash
alembic revision -m "describe your change here"
# Edit the generated file in alembic/versions/ to add upgrade()/downgrade() logic
```
