import os
import requests
from django.conf import settings
from functools import lru_cache

TMDB_BASE_URL = "https://api.themoviedb.org/3"


class TMDBApiError(Exception):
    """Custom exception for TMDB API errors."""
    pass


def get_tmdb_api_key() -> str:
    api_key = getattr(settings, "TMDB_API_KEY", "") or os.getenv("TMDB_API_KEY", "")
    if not api_key:
        raise TMDBApiError("TMDB_API_KEY is not configured")
    return api_key


@lru_cache(maxsize=64)
def fetch_movies_from_tmdb(page: int = 1) -> list[dict]:
    """
    Fetches a page of movies from TMDB Discover API and normalizes the data.
    Basic in-memory caching via lru_cache to avoid hitting TMDB too often.
    """
    api_key = get_tmdb_api_key()
    url = f"{TMDB_BASE_URL}/discover/movie"

    params = {
        "api_key": api_key,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "page": page,
        "vote_count.gte": 50,  # avoid obscure movies with almost no votes
    }

    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        raise TMDBApiError(f"TMDB API error: {resp.status_code} {resp.text}")

    data = resp.json()
    results = data.get("results", [])

    normalized = []
    for movie in results:
        normalized.append(
            {
                "id": movie.get("id"),
                "title": movie.get("title"),
                "overview": movie.get("overview"),
                "release_date": movie.get("release_date"),
                "original_language": movie.get("original_language"),
                "vote_average": movie.get("vote_average"),
                "vote_count": movie.get("vote_count"),
                "popularity": movie.get("popularity"),
                "genre_ids": movie.get("genre_ids", []),
                "poster_path": movie.get("poster_path"),
            }
        )

    return normalized
