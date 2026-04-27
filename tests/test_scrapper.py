from unittest.mock import patch, MagicMock

from modules.scrapers.epic import EpicGamesScraper
from modules.models import FreeGame
from config import EPIC_GAMES_REGION


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
                "fmtPrice": {
                    "originalPrice": "$19.99",
                    "discountPrice": "$0.00",
                },
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
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, epic_api_response)
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert len(games) == 1
        assert games[0].title == "Test Free Game"
        assert games[0].url == f"https://store.epicgames.com/{EPIC_GAMES_REGION}/p/test-free-game"
        assert games[0].end_date == "2024-01-31T15:00:00.000Z"
        assert games[0].description == "A free game for testing"
        assert games[0].image_url == "https://example.com/thumbnail.jpg"
        assert games[0].original_price == "$19.99"

    def test_excludes_paid_games(self):
        paid = _make_element(discount_price=1999)
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([paid]))
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert games == []

    def test_skips_mystery_games(self):
        mystery = _make_element(title="Mystery Game", discount_price=0)
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([mystery]))
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert games == []

    def test_returns_empty_on_api_error(self):
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(500)
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert games == []

    def test_uses_offer_slug_for_link(self):
        element = _make_element(discount_price=0, offer_slug="offer-slug-123")
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert "offer-slug-123" in games[0].url

    def test_falls_back_to_catalog_slug(self):
        element = _make_element(
            discount_price=0,
            offer_slug=None,
            catalog_slug="catalog-slug-456",
        )
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert "catalog-slug-456" in games[0].url

    def test_falls_back_to_product_slug(self):
        element = _make_element(
            discount_price=0,
            offer_slug=None,
            catalog_slug=None,
            product_slug="product-slug-789",
        )
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert "product-slug-789" in games[0].url

    def test_uses_default_link_when_no_slug(self):
        element = _make_element(
            discount_price=0,
            offer_slug=None,
            catalog_slug=None,
        )
        element.pop("productSlug", None)
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        expected_link = f"https://store.epicgames.com/{EPIC_GAMES_REGION}/free-games"
        assert games[0].url == expected_link

    def test_skips_game_with_no_promotional_offers(self):
        element = _make_element(discount_price=0, has_promotions=False)
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert games == []

    def test_uses_first_image_when_no_thumbnail(self):
        element = _make_element(
            discount_price=0,
            thumbnail_type="OfferImageWide",
            thumbnail_url="https://example.com/wide.jpg",
        )
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert games[0].image_url == "https://example.com/wide.jpg"

    def test_returns_empty_when_no_elements(self):
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([]))
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert games == []

    def test_original_price_populated_from_fmt_price(self):
        element = _make_element(discount_price=0, offer_slug="game-one")
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            games = EpicGamesScraper().fetch_free_games()

        assert games[0].original_price == "$19.99"

    def test_original_price_is_none_when_int_price_is_zero(self):
        element = _make_element(discount_price=0, offer_slug="always-free")
        element["price"]["totalPrice"]["originalPrice"] = 0
        element["price"]["totalPrice"]["fmtPrice"]["originalPrice"] = "0"
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            games = EpicGamesScraper().fetch_free_games()

        assert games[0].original_price is None

    def test_original_price_is_none_when_fmt_price_missing(self):
        element = _make_element(discount_price=0, offer_slug="game-one")
        del element["price"]["totalPrice"]["fmtPrice"]
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            games = EpicGamesScraper().fetch_free_games()

        assert games[0].original_price is None

    def test_multiple_free_games_returned(self):
        elements = [
            _make_element(title="Game One", discount_price=0, offer_slug="game-one"),
            _make_element(title="Game Two", discount_price=0, offer_slug="game-two"),
        ]
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response(elements))
            scraper = EpicGamesScraper()
            games = scraper.fetch_free_games()

        assert len(games) == 2
        titles = [g.title for g in games]
        assert "Game One" in titles
        assert "Game Two" in titles


# ---------------------------------------------------------------------------
# FreeGame model tests
# ---------------------------------------------------------------------------

class TestFreeGameModel:
    """Unit tests for the FreeGame dataclass and its from_dict factory."""

    def _base_dict(self, **overrides):
        data = {
            "title": "Sample Game",
            "store": "epic",
            "url": "https://store.epicgames.com/p/sample",
            "image_url": "https://example.com/img.jpg",
            "original_price": "$9.99",
            "end_date": "2024-01-31T15:00:00.000Z",
            "is_permanent": False,
            "description": "A game.",
        }
        data.update(overrides)
        return data

    def test_game_type_defaults_to_game(self):
        """FreeGame.game_type defaults to 'game' when not specified."""
        g = FreeGame(
            title="X",
            store="epic",
            url="https://store.epicgames.com/p/x",
            image_url="",
            original_price=None,
            end_date="",
            is_permanent=False,
            description="",
        )
        assert g.game_type == "game"

    def test_game_type_can_be_set_to_dlc(self):
        """FreeGame.game_type can be explicitly set to 'dlc'."""
        g = FreeGame(
            title="X DLC",
            store="steam",
            url="https://store.steampowered.com/app/1/",
            image_url="",
            original_price=None,
            end_date="",
            is_permanent=False,
            description="",
            game_type="dlc",
        )
        assert g.game_type == "dlc"

    def test_from_dict_preserves_game_type_game(self):
        """from_dict reads game_type='game' from the dict."""
        data = self._base_dict(game_type="game")
        g = FreeGame.from_dict(data)
        assert g.game_type == "game"

    def test_from_dict_preserves_game_type_dlc(self):
        """from_dict reads game_type='dlc' from the dict."""
        data = self._base_dict(game_type="dlc")
        g = FreeGame.from_dict(data)
        assert g.game_type == "dlc"

    def test_from_dict_defaults_game_type_to_game_when_absent(self):
        """from_dict falls back to 'game' when game_type key is missing."""
        data = self._base_dict()  # no game_type key
        g = FreeGame.from_dict(data)
        assert g.game_type == "game"

    def test_epic_scraper_returns_game_type_game(self):
        """EpicGamesScraper always sets game_type='game' on returned FreeGame objects."""
        element = _make_element(discount_price=0, offer_slug="test")
        with patch("modules.scrapers.epic.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, _make_api_response([element]))
            games = EpicGamesScraper().fetch_free_games()

        assert len(games) == 1
        assert games[0].game_type == "game"
