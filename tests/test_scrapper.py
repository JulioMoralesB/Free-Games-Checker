import pytest
from unittest.mock import patch, MagicMock

from modules import scrapper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_element(
    title="Test Game",
    discount_price=0,
    offer_slug=None,
    catalog_slug=None,
    product_slug=None,
    has_promotions=True,
    end_date="2024-01-31T15:00:00.000Z",
    thumbnail_type="Thumbnail",
    thumbnail_url="https://example.com/img.jpg",
    description="A game description",
):
    """Build a minimal Epic Games API element dict for testing."""
    element = {
        "title": title,
        "description": description,
        "price": {
            "totalPrice": {
                "discountPrice": discount_price,
                "originalPrice": 1999,
            }
        },
        "offerMappings": [{"pageSlug": offer_slug}] if offer_slug else [],
        "catalogNs": {
            "mappings": [{"pageSlug": catalog_slug}] if catalog_slug else []
        },
        "promotions": (
            {
                "promotionalOffers": [
                    {
                        "promotionalOffers": [
                            {
                                "discountSetting": {"discountPercentage": 0},
                                "endDate": end_date,
                            }
                        ]
                    }
                ]
            }
            if has_promotions
            else {"promotionalOffers": []}
        ),
        "keyImages": [{"type": thumbnail_type, "url": thumbnail_url}],
    }
    if product_slug is not None:
        element["productSlug"] = product_slug
    return element


def _make_api_response(elements):
    return {
        "data": {
            "Catalog": {
                "searchStore": {
                    "elements": elements
                }
            }
        }
    }


def _mock_response(status_code=200, json_data=None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    return mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFetchFreeGames:
    def test_returns_free_game(self, epic_api_response):
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, epic_api_response)
            games = scrapper.fetch_free_games()

        assert len(games) == 1
        assert games[0]["title"] == "Test Free Game"
        assert games[0]["link"] == "https://store.epicgames.com/es-MX/p/test-free-game"
        assert games[0]["end_date"] == "2024-01-31T15:00:00.000Z"
        assert games[0]["description"] == "A free game for testing"
        assert games[0]["thumbnail"] == "https://example.com/thumbnail.jpg"

    def test_excludes_paid_games(self):
        paid = _make_element(discount_price=1999)
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([paid]))
            games = scrapper.fetch_free_games()

        assert games == []

    def test_skips_mystery_games(self):
        mystery = _make_element(title="Mystery Game", discount_price=0)
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([mystery]))
            games = scrapper.fetch_free_games()

        assert games == []

    def test_returns_empty_on_api_error(self):
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(500)
            games = scrapper.fetch_free_games()

        assert games == []

    def test_uses_offer_slug_for_link(self):
        element = _make_element(discount_price=0, offer_slug="offer-slug-123")
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            games = scrapper.fetch_free_games()

        assert "offer-slug-123" in games[0]["link"]

    def test_falls_back_to_catalog_slug(self):
        element = _make_element(
            discount_price=0,
            offer_slug=None,
            catalog_slug="catalog-slug-456",
        )
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            games = scrapper.fetch_free_games()

        assert "catalog-slug-456" in games[0]["link"]

    def test_falls_back_to_product_slug(self):
        element = _make_element(
            discount_price=0,
            offer_slug=None,
            catalog_slug=None,
            product_slug="product-slug-789",
        )
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            games = scrapper.fetch_free_games()

        assert "product-slug-789" in games[0]["link"]

    def test_uses_default_link_when_no_slug(self):
        element = _make_element(
            discount_price=0,
            offer_slug=None,
            catalog_slug=None,
        )
        element.pop("productSlug", None)
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            games = scrapper.fetch_free_games()

        assert games[0]["link"] == "https://store.epicgames.com/es-MX/free-games"

    def test_skips_game_with_no_promotional_offers(self):
        element = _make_element(discount_price=0, has_promotions=False)
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            games = scrapper.fetch_free_games()

        assert games == []

    def test_uses_first_image_when_no_thumbnail(self):
        element = _make_element(
            discount_price=0,
            thumbnail_type="OfferImageWide",
            thumbnail_url="https://example.com/wide.jpg",
        )
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            games = scrapper.fetch_free_games()

        assert games[0]["thumbnail"] == "https://example.com/wide.jpg"

    def test_returns_empty_when_no_elements(self):
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([]))
            games = scrapper.fetch_free_games()

        assert games == []

    def test_multiple_free_games_returned(self):
        elements = [
            _make_element(title="Game One", discount_price=0, offer_slug="game-one"),
            _make_element(title="Game Two", discount_price=0, offer_slug="game-two"),
        ]
        with patch("modules.scrapper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response(elements))
            games = scrapper.fetch_free_games()

        assert len(games) == 2
        titles = [g["title"] for g in games]
        assert "Game One" in titles
        assert "Game Two" in titles
