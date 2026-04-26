import pytest

from modules.models import FreeGame


@pytest.fixture
def sample_game():
    """A sample FreeGame as returned by the scrapper."""
    return FreeGame(
        title="Test Free Game",
        store="epic",
        url="https://store.epicgames.com/es-MX/p/test-free-game",
        image_url="https://example.com/thumbnail.jpg",
        original_price=None,
        end_date="2024-01-31T15:00:00.000Z",
        is_permanent=False,
        description="A test game description",
    )


@pytest.fixture
def sample_games(sample_game):
    """A list containing one sample FreeGame."""
    return [sample_game]


@pytest.fixture
def epic_api_response():
    """
    A realistic Epic Games API response containing one free game element
    with all optional slug fields populated.
    """
    return {
        "data": {
            "Catalog": {
                "searchStore": {
                    "elements": [
                        {
                            "title": "Test Free Game",
                            "description": "A free game for testing",
                            "price": {
                                "totalPrice": {
                                    "discountPrice": 0,
                                    "originalPrice": 1999,
                                    "fmtPrice": {
                                        "originalPrice": "$19.99",
                                        "discountPrice": "$0.00",
                                    },
                                }
                            },
                            "offerMappings": [{"pageSlug": "test-free-game"}],
                            "catalogNs": {
                                "mappings": [{"pageSlug": "test-free-game-catalog"}]
                            },
                            "productSlug": "test-free-game-product",
                            "promotions": {
                                "promotionalOffers": [
                                    {
                                        "promotionalOffers": [
                                            {
                                                "discountSetting": {
                                                    "discountPercentage": 0
                                                },
                                                "endDate": "2024-01-31T15:00:00.000Z",
                                            }
                                        ]
                                    }
                                ]
                            },
                            "keyImages": [
                                {
                                    "type": "Thumbnail",
                                    "url": "https://example.com/thumbnail.jpg",
                                }
                            ],
                        }
                    ]
                }
            }
        }
    }
