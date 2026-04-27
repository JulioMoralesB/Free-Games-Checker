"""Shared review-score fetchers used by all store scrapers.

Each public function returns a single formatted string, or ``None`` when the
score is unavailable.  Callers aggregate results into a ``review_scores`` list
on the ``FreeGame`` model.

Supported formats
-----------------
- ``"Very Positive"``       — Steam-style user-review label (passed through as-is)
- ``"Metascore: 83"``       — Metacritic critic score (0–100)
- ``"OpenCritic: 78"``      — OpenCritic critic score (0–100)
"""

import json
import logging
import re
import unicodedata

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Metacritic
# ---------------------------------------------------------------------------

_METACRITIC_BASE = "https://www.metacritic.com/game"

# Mimic a real browser so Metacritic serves the full HTML page with JSON-LD.
_MC_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def make_metacritic_slug(title: str) -> str:
    """Convert a game title to a Metacritic URL slug.

    Examples
    --------
    >>> make_metacritic_slug("The Witcher 3: Wild Hunt")
    'the-witcher-3-wild-hunt'
    >>> make_metacritic_slug("Baldur's Gate 3")
    'baldurs-gate-3'
    """
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = ascii_title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug


def fetch_metacritic_score(title: str) -> str | None:
    """Return ``"Metascore: 83"`` for *title* scraped from Metacritic, or ``None``.

    Metacritic embeds the critic score as JSON-LD structured data in the page
    HTML, so no API key is required.  Any network or parsing failure is logged
    as a warning and returns ``None`` so a single game never blocks the scrape.
    """
    slug = make_metacritic_slug(title)
    url = f"{_METACRITIC_BASE}/{slug}/"
    logger.info("Metacritic: fetching score for %r → %s", title, url)

    try:
        resp = requests.get(url, headers=_MC_HEADERS, timeout=10)
        if resp.status_code != 200:
            logger.info(
                "Metacritic: HTTP %s for %r — skipping review score",
                resp.status_code, title,
            )
            return None

        blocks = re.findall(
            r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
            resp.text,
            re.DOTALL,
        )
        for raw_block in blocks:
            try:
                data = json.loads(raw_block)
            except json.JSONDecodeError:
                continue

            agg = data.get("aggregateRating") or {}
            value = agg.get("ratingValue")
            if value is not None:
                try:
                    score = int(value)
                    logger.info("Metacritic: %r → Metascore %d", title, score)
                    return f"Metascore: {score}"
                except (ValueError, TypeError):
                    continue

        logger.info("Metacritic: no aggregateRating found for %r", title)

    except Exception as exc:
        logger.warning("Metacritic: failed to fetch score for %r: %s", title, exc)

    return None


# ---------------------------------------------------------------------------
# OpenCritic
# ---------------------------------------------------------------------------

_OC_SEARCH_URL = "https://api.opencritic.com/api/game/search"

# OpenCritic's public (unauthenticated) search API — no key required.
_OC_HEADERS = {
    "User-Agent": "FreeGamesNotifier/1.0 (github.com/JulioMoralesB/free-games-notifier)",
    "Accept": "application/json",
}


def _normalise(title: str) -> str:
    """Lowercase ASCII slug for fuzzy name matching against OpenCritic results."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", ascii_title).lower()).strip()


def fetch_opencritic_score(title: str) -> str | None:
    """Return ``"OpenCritic: 78"`` for *title* via the OpenCritic search API, or ``None``.

    Uses the public unauthenticated ``/api/game/search`` endpoint — no API key
    is required.  Picks the result whose name best matches the query; falls back
    to the highest-ranked result.  Any failure returns ``None`` gracefully.
    """
    logger.info("OpenCritic: fetching score for %r", title)

    try:
        resp = requests.get(
            _OC_SEARCH_URL,
            params={"criteria": title},
            headers=_OC_HEADERS,
            timeout=8,
        )
        if resp.status_code != 200:
            logger.info(
                "OpenCritic: HTTP %s for %r — skipping review score",
                resp.status_code, title,
            )
            return None

        results = resp.json()
        if not isinstance(results, list) or not results:
            logger.info("OpenCritic: no results for %r", title)
            return None

        # Prefer an exact name match; fall back to the first (highest-ranked) result.
        query_norm = _normalise(title)
        match = next(
            (r for r in results if _normalise(r.get("name", "")) == query_norm),
            results[0],
        )

        score = match.get("score")
        if score is None:
            logger.info("OpenCritic: %r matched %r but score is None", title, match.get("name"))
            return None

        try:
            score_int = int(score)
            logger.info("OpenCritic: %r → %d", title, score_int)
            return f"OpenCritic: {score_int}"
        except (ValueError, TypeError):
            return None

    except Exception as exc:
        logger.warning("OpenCritic: failed to fetch score for %r: %s", title, exc)

    return None
