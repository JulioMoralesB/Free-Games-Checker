"""Integration tests for the API running in Docker container.

These tests verify that the config endpoint returns values matching the environment
by running a Python one-liner (`python -c`) inside the container via `docker compose exec`.
This works regardless of whether ports are exposed and mirrors how services inside a cluster communicate.

Both sources are independent:
  - Expected: values from the .env file (loaded on the host by the test)
  - Actual: values returned by the container's /config endpoint

To run:
    docker compose up -d
    pytest tests/test_api_integration.py -v
"""

import json
import os
import subprocess

import pytest
from dotenv import load_dotenv


# Load environment variables from .env file (same as what compose.yaml uses)
load_dotenv()

CONTAINER_NAME = "free-games-notifier"
_COMPOSE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_json(path):
    """Fetch an API endpoint by running a Python one-liner inside the container."""
    port = int(os.getenv("API_PORT", 8000))
    script = (
        "import urllib.request, json, sys; "
        f"res = urllib.request.urlopen('http://localhost:{port}{path}'); "
        "print(json.dumps(json.loads(res.read())))"
    )
    result = subprocess.run(
        [
            "docker", "compose", "exec", "-T",
            CONTAINER_NAME,
            "python", "-c", script,
        ],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=_COMPOSE_DIR,
    )
    if result.returncode != 0:
        pytest.fail(
            f"Could not reach API inside container: "
            f"{result.stderr.strip() or 'python returned non-zero exit code'}"
        )
    return json.loads(result.stdout)


@pytest.mark.integration
class TestHealthEndpoint:
    """Verify /health endpoint returns healthy status."""

    def test_health_endpoint(self):
        """Verify /health returns healthy status."""
        resp_json = get_json("/health")

        assert resp_json["status"] == "healthy", f"Expected status 'healthy' but got '{resp_json['status']}'"
        # Do not require the external Epic Games API to be healthy to avoid flaky tests.
        # Instead, verify that the field exists and has a string status.
        assert "epic_games_api" in resp_json, "Expected 'epic_games_api' field in health response"
        assert isinstance(resp_json["epic_games_api"], str), \
            f"Expected epic_games_api to be a string but got {type(resp_json['epic_games_api'])!r}"
        db_host = os.getenv("DB_HOST")
        if db_host:
            assert resp_json["database"] == "healthy", f"Expected database 'healthy' but got '{resp_json['database']}'"


@pytest.mark.integration
class TestConfigEndpointMatchesEnv:
    """Verify /config endpoint returns values matching environment variables."""

    def test_date_format_matches_env(self):
        """Verify DATE_FORMAT in /config matches the env variable."""
        expected_date_format = os.getenv("DATE_FORMAT", "%d de %B de %Y a las %I:%M %p")

        config = get_json("/config")

        assert config["date_format"] == expected_date_format, \
            f"Expected DATE_FORMAT '{expected_date_format}' but got '{config['date_format']}'"

    def test_timezone_matches_env(self):
        """Verify TIMEZONE in /config matches the env variable."""
        expected_timezone = os.getenv("TIMEZONE", "America/Mexico_City")

        config = get_json("/config")

        assert config["timezone"] == expected_timezone, \
            f"Expected TIMEZONE '{expected_timezone}' but got '{config['timezone']}'"

    def test_locale_matches_env(self):
        """Verify LOCALE in /config matches the env variable."""
        expected_locale = os.getenv("LOCALE", "es_ES.UTF-8")

        config = get_json("/config")

        assert config["locale"] == expected_locale, \
            f"Expected LOCALE '{expected_locale}' but got '{config['locale']}'"

    def test_schedule_time_matches_env(self):
        """Verify SCHEDULE_TIME in /config matches the env variable."""
        expected_schedule = os.getenv("SCHEDULE_TIME", "12:00")

        config = get_json("/config")

        assert config["schedule_time"] == expected_schedule, \
            f"Expected SCHEDULE_TIME '{expected_schedule}' but got '{config['schedule_time']}'"

    def test_epic_games_region_matches_env(self):
        """Verify EPIC_GAMES_REGION in /config matches the env variable."""
        expected_region = os.getenv("EPIC_GAMES_REGION", "es-MX")

        config = get_json("/config")

        assert config["epic_games_region"] == expected_region, \
            f"Expected EPIC_GAMES_REGION '{expected_region}' but got '{config['epic_games_region']}'"
