import pytest
from unittest.mock import patch, MagicMock
import requests as requests_lib

from modules import notifier


VALID_WEBHOOK = "https://discord.com/api/webhooks/123456789/token_abc"


# ---------------------------------------------------------------------------
# Tests for _get_safe_webhook_identifier
# ---------------------------------------------------------------------------

class TestGetSafeWebhookIdentifier:
    def test_redacts_token_from_discord_url(self):
        result = notifier._get_safe_webhook_identifier(VALID_WEBHOOK)
        assert "token_abc" not in result
        assert "123456789" in result
        assert result == "discord.com/api/webhooks/123456789"

    def test_returns_unknown_for_empty_string(self):
        result = notifier._get_safe_webhook_identifier("")
        assert result == "unknown-webhook"

    def test_returns_unknown_for_none(self):
        result = notifier._get_safe_webhook_identifier(None)
        assert result == "unknown-webhook"

    def test_returns_host_for_non_discord_url(self):
        result = notifier._get_safe_webhook_identifier("https://example.com/hook")
        assert result == "example.com"

    def test_handles_url_without_standard_webhook_path(self):
        result = notifier._get_safe_webhook_identifier("https://myservice.com/api/notify")
        assert result == "myservice.com"


# ---------------------------------------------------------------------------
# Tests for send_discord_message
# ---------------------------------------------------------------------------

class TestSendDiscordMessage:
    def _make_response(self, status_code=204):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.text = ""
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def test_raises_when_webhook_url_not_configured(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", None):
            with pytest.raises(ValueError, match="webhook URL not configured"):
                notifier.send_discord_message(sample_games)

    def test_sends_post_request_to_webhook(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == VALID_WEBHOOK
        assert "json" in kwargs

    def test_embed_contains_game_title(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["embeds"][0]["title"] == "Test Free Game"

    def test_embed_contains_game_link(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["embeds"][0]["url"] == sample_games[0]["link"]

    def test_embed_contains_thumbnail(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["embeds"][0]["image"]["url"] == sample_games[0]["thumbnail"]

    def test_embed_footer_contains_end_date_prefix(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["embeds"][0]["footer"]["text"].startswith("Finaliza el ")

    def test_embed_author_is_epic_games_store(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["embeds"][0]["author"]["name"] == "Epic Games Store"

    def test_raises_on_http_error_status(self, sample_games):
        mock_resp = self._make_response(400)
        mock_resp.raise_for_status.side_effect = requests_lib.exceptions.HTTPError(
            "400 Bad Request"
        )
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post", return_value=mock_resp):
            with pytest.raises(requests_lib.exceptions.HTTPError):
                notifier.send_discord_message(sample_games)

    def test_raises_on_timeout(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch(
                 "modules.notifier.requests.post",
                 side_effect=requests_lib.exceptions.Timeout(),
             ):
            with pytest.raises(requests_lib.exceptions.Timeout):
                notifier.send_discord_message(sample_games)

    def test_raises_on_connection_error(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch(
                 "modules.notifier.requests.post",
                 side_effect=requests_lib.exceptions.ConnectionError(),
             ):
            with pytest.raises(requests_lib.exceptions.ConnectionError):
                notifier.send_discord_message(sample_games)

    def test_sends_multiple_game_embeds(self, sample_game):
        game2 = dict(sample_game)
        game2["title"] = "Second Free Game"
        games = [sample_game, game2]

        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(games)

        _, kwargs = mock_post.call_args
        assert len(kwargs["json"]["embeds"]) == 2

    def test_raises_on_missing_game_key(self):
        bad_game = {"title": "Incomplete Game"}  # missing end_date, link, etc.
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK):
            with pytest.raises(KeyError):
                notifier.send_discord_message([bad_game])
