from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

_FIELD_ALIASES: dict[str, str] = {
    "link": "url",
    "thumbnail": "image_url",
}

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
    description     : A short description of the game, or ``None`` if not available.

    """

    title: str
    store: str
    url: str
    image_url: str
    original_price: Optional[str]
    end_date: str
    is_permanent: bool
    description: Optional[str] = field(default="")

    # ------------------------------------------------------------------
    # Dict-style access – keeps existing consumers working without changes.
    # ------------------------------------------------------------------
 
    def __getitem__(self, key: str):  # type: ignore[override]
        resolved = _FIELD_ALIASES.get(key, key)
        try:
            return getattr(self, resolved)
        except AttributeError:
            raise KeyError(key) from None
 
    def get(self, key: str, default=None):
        try:
            return self[key]
        except KeyError:
            return default
 