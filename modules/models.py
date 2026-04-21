from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Optional


@dataclass
class FreeGame:
    """A free-game promotion from any supported store.

    Fields
    ------
    title           : Display name of the game.
    store           : Identifier of the store that is offering the game for free, e.g. "epic".
    url             : URL to the game's store page.
    image_url       : URL to an image representing the game, e.g. a thumbnail.
    original_price  : The original price of the game, as a string, or ``None`` if not available. (e.g. "$19.99")
    end_date        : ISO-8601 UTC string for when the promotion ends.
    is_permanent    : Whether the promotion is permanent, as a boolean.
    description     : A short description of the game.
    """

    title: str
    store: str
    url: str
    image_url: str
    original_price: Optional[str]
    end_date: str
    is_permanent: bool
    description: str = ""
    review_score: Optional[str] = None

    def to_dict(self) -> dict:
        """Return a plain dict representation of this FreeGame."""
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FreeGame":
        """Create a FreeGame from a dict, accepting both current and legacy field names."""
        return cls(
            title=data.get("title", ""),
            store=data.get("store", "epic"),
            url=data.get("url") or data.get("link", ""),
            image_url=data.get("image_url") or data.get("thumbnail", ""),
            original_price=data.get("original_price"),
            end_date=data.get("end_date", ""),
            is_permanent=data.get("is_permanent", False),
            description=data.get("description", ""),
            review_score=data.get("review_score"),
        )
 