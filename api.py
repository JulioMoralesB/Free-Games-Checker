"""REST API for the Free Games Notifier service."""

import time
import logging
from typing import List, Optional

import requests as requests_lib
from fastapi import FastAPI, HTTPException, Query, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from config import (
    API_KEY,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    DATA_FILE_PATH,
    DATE_FORMAT,
    ENABLE_HEALTHCHECK,
    EPIC_GAMES_API_URL,
    EPIC_GAMES_REGION,
    HEALTHCHECK_INTERVAL,
    HEALTHCHECK_URL,
    LOCALE,
    SCHEDULE_TIME,
    TIMEZONE,
)


# ---------------------------------------------------------------------------
# Pydantic response models (for OpenAPI / Swagger documentation)
# ---------------------------------------------------------------------------


class GameItem(BaseModel):
    """A free game as returned by the scraper."""
    title: str = Field(..., description="Name of the free game", examples=["Celeste"])
    link: str = Field(..., description="Epic Games Store URL for the game")
    end_date: str = Field(..., description="ISO-8601 timestamp when the free promotion ends", examples=["2024-01-31T15:00:00.000Z"])
    description: str = Field(..., description="Short description of the game")
    thumbnail: str = Field(..., description="URL to the game's thumbnail image")


class HealthResponse(BaseModel):
    """Response from the health check endpoint."""
    status: str = Field(..., description="Overall health status", examples=["healthy", "unhealthy"])
    epic_games_api: str = Field(..., description="Epic Games API reachability", examples=["healthy", "unhealthy"])
    database: str = Field(..., description="Database connectivity status", examples=["healthy", "unhealthy", "not_configured"])


class GamesLatestResponse(BaseModel):
    """Response from the latest games endpoint."""
    games: List[GameItem] = Field(..., description="List of the most recently fetched games")
    count: int = Field(..., description="Number of games returned", examples=[3])


class GamesHistoryResponse(BaseModel):
    """Response from the paginated game history endpoint."""
    games: List[GameItem] = Field(..., description="List of games for the current page")
    total: int = Field(..., description="Total number of games in storage", examples=[42])
    limit: int = Field(..., description="Maximum number of games per page", examples=[20])
    offset: int = Field(..., description="Number of games skipped", examples=[0])


class ResendResponse(BaseModel):
    """Response after re-sending a Discord notification."""
    status: str = Field(..., description="Result of the operation", examples=["success"])
    games_sent: int = Field(..., description="Number of games included in the notification", examples=[2])


class MetricsResponse(BaseModel):
    """Service metrics snapshot."""
    uptime_seconds: float = Field(..., description="Seconds since the API server started", examples=[3600.5])
    games_processed: int = Field(..., description="Total games processed since startup", examples=[12])
    discord_notifications_sent: int = Field(..., description="Successful Discord notifications sent", examples=[5])
    discord_notification_errors: int = Field(..., description="Failed Discord notification attempts", examples=[1])
    errors: int = Field(..., description="Total error count across all operations", examples=[2])


class ConfigResponse(BaseModel):
    """Non-secret runtime configuration."""
    epic_games_api_url: str = Field(..., description="Epic Games API endpoint URL")
    epic_games_region: str = Field(..., description="Region code used in store links", examples=["es-MX"])
    data_file_path: str = Field(..., description="Path to the JSON storage file")
    enable_healthcheck: bool = Field(..., description="Whether the external health check ping is enabled")
    healthcheck_url: Optional[str] = Field(None, description="URL of the external health check monitor")
    healthcheck_interval_minutes: int = Field(..., description="Interval in minutes between health check pings", examples=[1])
    db_host: Optional[str] = Field(None, description="PostgreSQL host (None when DB is not configured)")
    db_port: int = Field(..., description="PostgreSQL port", examples=[5432])
    db_name: Optional[str] = Field(None, description="PostgreSQL database name")
    db_user: Optional[str] = Field(None, description="PostgreSQL user")
    timezone: str = Field(..., description="Configured timezone for date display", examples=["America/Mexico_City"])
    locale: str = Field(..., description="Locale used for date formatting", examples=["es_ES.UTF-8"])
    schedule_time: str = Field(..., description="Daily check time in HH:MM format", examples=["12:00"])
    date_format: str = Field(..., description="strftime format string for promotion end dates")


class CheckE2EResponse(BaseModel):
    """Response from the end-to-end check endpoint."""
    games_fetched: int = Field(..., description="Number of free games fetched from Epic Games", examples=[2])
    games: List[GameItem] = Field(..., description="Full list of fetched game objects")
    already_in_storage: List[str] = Field(..., description="Titles of games that were already saved in storage")
    new_games: List[str] = Field(..., description="Titles of games not yet in storage")
    notification_status: str = Field(..., description="Discord notification result", examples=["sent", "skipped", "failed: ..."])


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = Field(..., description="Human-readable error message")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Metrics state (module-level, shared across requests)
# ---------------------------------------------------------------------------

_start_time = time.time()
_metrics = {
    "games_processed": 0,
    "discord_notifications_sent": 0,
    "discord_notification_errors": 0,
    "errors": 0,
}


def increment_metric(key: str, amount: int = 1):
    """Safely increment a metric counter."""
    if key in _metrics:
        _metrics[key] += amount


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Free Games Notifier API",
    description="REST API for monitoring and managing the Free Games Notifier service.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# API Key authentication
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def _verify_api_key(api_key: str = Security(_api_key_header)):
    """Validate the API key for mutating endpoints.

    When ``API_KEY`` is not set the check is skipped so that local /
    development deployments work out-of-the-box without auth.
    """
    if not API_KEY:
        return
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health():
    """Active health check: Epic Games API reachability and database connectivity."""
    result = {"epic_games_api": "unknown", "database": "not_configured"}

    # Check Epic Games API
    try:
        resp = requests_lib.get(EPIC_GAMES_API_URL, timeout=10)
        result["epic_games_api"] = "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception:
        result["epic_games_api"] = "unhealthy"

    # Check database if configured
    if DB_HOST:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
            conn.close()
            result["database"] = "healthy"
        except Exception:
            result["database"] = "unhealthy"

    overall = "healthy"
    if result["epic_games_api"] != "healthy":
        overall = "unhealthy"
    if DB_HOST and result["database"] != "healthy":
        overall = "unhealthy"
    result["status"] = overall
    return result


@app.get(
    "/games/latest",
    response_model=GamesLatestResponse,
    responses={500: {"model": ErrorResponse, "description": "Failed to load games from storage"}},
)
async def games_latest():
    """Return the most recently fetched games from the configured storage backend."""
    from modules.storage import load_previous_games

    try:
        games = load_previous_games()
        return {"games": games, "count": len(games)}
    except Exception as e:
        logger.error("Failed to load latest games: %s", e)
        increment_metric("errors")
        raise HTTPException(status_code=500, detail="Failed to load games")


@app.get(
    "/games/history",
    response_model=GamesHistoryResponse,
    responses={500: {"model": ErrorResponse, "description": "Failed to load game history"}},
)
async def games_history(
    limit: int = Query(default=20, ge=1, le=100, description="Max number of games to return"),
    offset: int = Query(default=0, ge=0, description="Number of games to skip"),
):
    """Paginated access to all past fetched games.

    Query parameters:
    - **limit**: Max number of games to return (1–100, default: 20)
    - **offset**: Number of games to skip (default: 0)
    """
    from modules.storage import load_previous_games

    try:
        all_games = load_previous_games()
        total = len(all_games)
        page = all_games[offset : offset + limit]
        return {"games": page, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        logger.error("Failed to load game history: %s", e)
        increment_metric("errors")
        raise HTTPException(status_code=500, detail="Failed to load game history")


@app.post(
    "/notify/discord/resend",
    response_model=ResendResponse,
    dependencies=[Security(_verify_api_key)],
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "No games available to resend"},
        500: {"model": ErrorResponse, "description": "Failed to send Discord notification"},
    },
)
async def notify_discord_resend():
    """Re-send the latest fetched games to the Discord webhook."""
    from modules.storage import load_previous_games
    from modules.notifier import send_discord_message

    try:
        games = load_previous_games()
    except Exception as e:
        logger.error("Failed to load games for resend: %s", e)
        increment_metric("errors")
        raise HTTPException(status_code=500, detail="Failed to load games")

    if not games:
        raise HTTPException(status_code=404, detail="No games available to resend")

    try:
        send_discord_message(games)
        increment_metric("discord_notifications_sent")
        return {"status": "success", "games_sent": len(games)}
    except Exception as e:
        logger.error("Failed to resend Discord notification: %s", e)
        increment_metric("discord_notification_errors")
        increment_metric("errors")
        raise HTTPException(status_code=500, detail=f"Failed to send Discord notification: {e}")


@app.get("/metrics", response_model=MetricsResponse)
async def metrics():
    """Basic service metrics: uptime, games processed, notifications sent, errors."""
    uptime_seconds = time.time() - _start_time
    return {
        "uptime_seconds": round(uptime_seconds, 2),
        **_metrics,
    }


@app.get("/config", response_model=ConfigResponse)
async def config_endpoint():
    """Expose non-secret runtime configuration."""
    return {
        "epic_games_api_url": EPIC_GAMES_API_URL,
        "epic_games_region": EPIC_GAMES_REGION,
        "data_file_path": DATA_FILE_PATH,
        "enable_healthcheck": ENABLE_HEALTHCHECK,
        "healthcheck_url": HEALTHCHECK_URL,
        "healthcheck_interval_minutes": HEALTHCHECK_INTERVAL,
        "db_host": DB_HOST,
        "db_port": DB_PORT,
        "db_name": DB_NAME,
        "db_user": DB_USER,
        "timezone": TIMEZONE,
        "locale": LOCALE,
        "schedule_time": SCHEDULE_TIME,
        "date_format": DATE_FORMAT,
    }


@app.post(
    "/check",
    response_model=CheckE2EResponse,
    dependencies=[Security(_verify_api_key)],
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "No free games found from Epic Games API"},
        500: {"model": ErrorResponse, "description": "Failed to fetch games from Epic Games API"},
    },
)
async def check_e2e():
    """End-to-end test: fetch games, check DB presence, and send Discord notification regardless.

    This endpoint runs the full flow even when the games already exist in the
    database so you can test the pipeline without deleting stored data.
    """
    from modules.scrapper import fetch_free_games
    from modules.storage import load_previous_games
    from modules.notifier import send_discord_message

    # 1. Fetch current free games from Epic Games
    try:
        current_games = fetch_free_games()
        increment_metric("games_processed", len(current_games))
    except Exception as e:
        logger.error("E2E check – failed to fetch games: %s", e)
        increment_metric("errors")
        raise HTTPException(status_code=500, detail=f"Failed to fetch games: {e}")

    if not current_games:
        raise HTTPException(status_code=404, detail="No free games found from Epic Games API")

    # 2. Check which games already exist in storage
    try:
        previous_games = load_previous_games()
    except Exception as e:
        logger.error("E2E check – failed to load previous games: %s", e)
        previous_games = []

    already_saved = [g for g in current_games if g in previous_games]
    new_games = [g for g in current_games if g not in previous_games]

    # 3. Send Discord notification regardless of DB state
    notification_status = "skipped"
    try:
        send_discord_message(current_games)
        notification_status = "sent"
        increment_metric("discord_notifications_sent")
    except Exception as e:
        logger.error("E2E check – Discord notification failed: %s", e)
        notification_status = f"failed: {e}"
        increment_metric("discord_notification_errors")
        increment_metric("errors")

    return {
        "games_fetched": len(current_games),
        "games": current_games,
        "already_in_storage": [g.get("title", "") for g in already_saved],
        "new_games": [g.get("title", "") for g in new_games],
        "notification_status": notification_status,
    }
