import pytest


@pytest.fixture
def sample_game():
    """A sample free game dictionary as returned by the scrapper."""
    return {
        "title": "Test Free Game",
        "link": "https://store.epicgames.com/es-MX/p/test-free-game",
        "end_date": "2024-01-31T15:00:00.000Z",
        "description": "A test game description",
        "thumbnail": "https://example.com/thumbnail.jpg",
    }


@pytest.fixture
def sample_games(sample_game):
    """A list containing one sample free game."""
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
