import pytest
from unittest.mock import patch, MagicMock
import requests as requests_lib

from modules import notifier
from modules.models import FreeGame


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
        assert payload["embeds"][0]["url"] == sample_games[0].url

    def test_embed_contains_thumbnail(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["embeds"][0]["image"]["url"] == sample_games[0].image_url

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

    def test_embed_author_has_epic_store_icon(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert "icon_url" in payload["embeds"][0]["author"]
        assert "icons8.com" in payload["embeds"][0]["author"]["icon_url"]
        assert "epic-games" in payload["embeds"][0]["author"]["icon_url"]

    def test_embed_author_has_steam_store_icon(self):
        game = FreeGame(
            title="Steam Game",
            store="steam",
            url="https://store.steampowered.com/app/123/",
            image_url="https://example.com/img.jpg",
            original_price="$9.99",
            end_date="2024-01-31T15:00:00.000Z",
            is_permanent=False,
            description="",
        )
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message([game])

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert "icon_url" in payload["embeds"][0]["author"]
        assert "wikimedia.org" in payload["embeds"][0]["author"]["icon_url"]
        assert "Steam_icon_logo" in payload["embeds"][0]["author"]["icon_url"]

    def test_embed_includes_review_score_field_when_present(self):
        game = FreeGame(
            title="Steam Game",
            store="steam",
            url="https://store.steampowered.com/app/123/",
            image_url="https://example.com/img.jpg",
            original_price="$9.99",
            end_date="2024-01-31T15:00:00.000Z",
            is_permanent=False,
            description="",
            review_score="Very Positive",
        )
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message([game])

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        fields = payload["embeds"][0].get("fields", [])
        assert any(
            f["name"] == "💬 User Reviews:"
            and "Very Positive" in f["value"]
            and "⭐" in f["value"]
            for f in fields
        )

    def test_embed_no_review_score_field_when_absent(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert "fields" not in payload["embeds"][0]

    def test_content_message_uses_epic_store_name(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        assert "Epic Games Store" in kwargs["json"]["content"]

    def test_content_message_uses_steam_store_name(self):
        game = FreeGame(
            title="Steam Game",
            store="steam",
            url="https://store.steampowered.com/app/123/",
            image_url="https://example.com/img.jpg",
            original_price="$9.99",
            end_date="2024-01-31T15:00:00.000Z",
            is_permanent=False,
            description="",
        )
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message([game])

        _, kwargs = mock_post.call_args
        assert "Steam" in kwargs["json"]["content"]

    def test_content_message_is_generic_for_multi_store_batch(self, sample_game):
        import dataclasses
        steam_game = dataclasses.replace(sample_game, store="steam", title="Steam Game")
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message([sample_game, steam_game])

        _, kwargs = mock_post.call_args
        content = kwargs["json"]["content"]
        assert "Epic Games Store" not in content
        assert "Steam" not in content

    def test_embed_author_url_uses_epic_games_region(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.EPIC_GAMES_REGION", "de-DE"), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["embeds"][0]["author"]["url"] == "https://store.epicgames.com/de-DE/free-games"

    def test_unknown_timezone_falls_back_to_utc(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.TIMEZONE", "Invalid/Timezone"), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            # Should not raise; falls back to UTC silently
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        # Footer should still contain "UTC" when the timezone falls back
        assert "UTC" in payload["embeds"][0]["footer"]["text"]

    def test_embed_footer_contains_configured_timezone(self, sample_games):
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.TIMEZONE", "Europe/London"), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert "(Europe/London)" in payload["embeds"][0]["footer"]["text"]

    def test_embed_footer_respects_date_format(self, sample_games):
        custom_format = "%Y/%m/%d"
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.DATE_FORMAT", custom_format), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        footer_text = payload["embeds"][0]["footer"]["text"]
        # end_date is "2024-01-31T15:00:00.000Z"; with custom format the date portion is "2024/01/31"
        assert "2024/01/31" in footer_text

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
        import dataclasses
        game2 = dataclasses.replace(sample_game, title="Second Free Game")
        games = [sample_game, game2]

        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(games)

        _, kwargs = mock_post.call_args
        assert len(kwargs["json"]["embeds"]) == 2

    def test_raises_on_invalid_end_date(self):
        from modules.models import FreeGame
        bad_game = FreeGame(
            title="Incomplete Game",
            store="epic",
            url="https://store.epicgames.com/p/incomplete",
            image_url="",
            original_price=None,
            end_date="not-a-valid-date",
            is_permanent=False,
            description="",
        )
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK):
            with pytest.raises(ValueError):
                notifier.send_discord_message([bad_game])

    def test_embed_footer_unknown_end_date_when_empty_and_not_permanent(self):
        """Games with no end_date and is_permanent=False show a 'not available' message."""
        # dataclasses.replace with no replacements is a no-op; use FreeGame() directly.
        game = FreeGame(
            title="Steam Game",
            store="steam",
            url="https://store.steampowered.com/app/123/",
            image_url="https://example.com/img.jpg",
            original_price="$9.99",
            end_date="",
            is_permanent=False,
            description="",
        )
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message([game])

        _, kwargs = mock_post.call_args
        footer = kwargs["json"]["embeds"][0]["footer"]["text"]
        assert footer == "Fecha de fin no disponible"

    def test_embed_footer_permanent_game(self):
        """Games with is_permanent=True show the permanent promotion message."""
        game = FreeGame(
            title="Free Forever Game",
            store="epic",
            url="https://store.epicgames.com/p/free-forever",
            image_url="https://example.com/img.jpg",
            original_price=None,
            end_date="",
            is_permanent=True,
            description="",
        )
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message([game])

        _, kwargs = mock_post.call_args
        footer = kwargs["json"]["embeds"][0]["footer"]["text"]
        assert footer == "Gratis de forma permanente"


class TestSendDiscordMessageWebhookOverride:
    """Tests for the optional webhook_url override in send_discord_message."""

    def _make_response(self, status_code=204):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.text = ""
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def test_override_url_is_used_instead_of_env_var(self, sample_games):
        """When webhook_url is provided, requests.post() uses it, not DISCORD_WEBHOOK_URL."""
        override_url = "https://discord.com/api/webhooks/9999/override-token"
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games, webhook_url=override_url)

        args, _ = mock_post.call_args
        assert args[0] == override_url
        assert args[0] != VALID_WEBHOOK

    def test_env_var_used_when_no_override(self, sample_games):
        """When webhook_url is not provided, requests.post() uses DISCORD_WEBHOOK_URL."""
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games)

        args, _ = mock_post.call_args
        assert args[0] == VALID_WEBHOOK

    def test_raises_on_non_discord_override_url(self, sample_games):
        """User-supplied webhook URLs pointing to non-Discord hosts are rejected."""
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK):
            with pytest.raises(ValueError, match="discord.com"):
                notifier.send_discord_message(
                    sample_games,
                    webhook_url="https://evil.com/api/webhooks/123/token",
                )

    def test_raises_on_non_https_override_url(self, sample_games):
        """User-supplied webhook URLs not using HTTPS are rejected."""
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK):
            with pytest.raises(ValueError, match="HTTPS"):
                notifier.send_discord_message(
                    sample_games,
                    webhook_url="http://discord.com/api/webhooks/123/token",
                )

    def test_raises_on_override_url_with_wrong_path(self, sample_games):
        """User-supplied webhook URLs without /api/webhooks/ path are rejected."""
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK):
            with pytest.raises(ValueError, match="/api/webhooks/"):
                notifier.send_discord_message(
                    sample_games,
                    webhook_url="https://discord.com/not/a/webhook",
                )

    def test_discordapp_com_host_is_allowed(self, sample_games):
        """discord.com and discordapp.com are both valid webhook hosts."""
        alt_host_url = "https://discordapp.com/api/webhooks/123/token"
        with patch("modules.notifier.DISCORD_WEBHOOK_URL", VALID_WEBHOOK), \
             patch("modules.notifier.requests.post") as mock_post:
            mock_post.return_value = self._make_response(204)
            notifier.send_discord_message(sample_games, webhook_url=alt_host_url)

        args, _ = mock_post.call_args
        assert args[0] == alt_host_url
