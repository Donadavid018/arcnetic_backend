from collections import defaultdict
from statistics import mean

# Basic mapping for a few common genres (TMDB genre IDs)
TMDB_GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    18: "Drama",
    27: "Horror",
    10749: "Romance",
    878: "Science Fiction",
    53: "Thriller",
}


def parse_filter_query(filter_str: str | None) -> dict:
    """
    Parses filter string like: "year:2023,language:en,genre:Action"
    into a dict: {"year": "2023", "language": "en", "genre": "Action"}
    """
    filters = {}
    if not filter_str:
        return filters

    parts = filter_str.split(",")
    for part in parts:
        if ":" in part:
            key, value = part.split(":", 1)
            filters[key.strip().lower()] = value.strip()
    return filters


def apply_filters(movies: list[dict], filters: dict) -> list[dict]:
    if not filters:
        return movies

    def match(movie: dict) -> bool:
        # Year filter
        year = filters.get("year")
        if year and movie.get("release_date"):
            if not str(movie["release_date"]).startswith(str(year)):
                return False

        # Language filter
        lang = filters.get("language")
        if lang and movie.get("original_language") != lang:
            return False

        # Minimum rating
        min_rating = filters.get("min_rating")
        if min_rating:
            try:
                min_rating_val = float(min_rating)
                if (movie.get("vote_average") or 0) < min_rating_val:
                    return False
            except ValueError:
                pass

        # Genre by name
        genre_name = filters.get("genre")
        if genre_name:
            genre_ids = movie.get("genre_ids", [])
            names = {TMDB_GENRE_MAP.get(gid, "").lower() for gid in genre_ids}
            if genre_name.lower() not in names:
                return False

        return True

    return [m for m in movies if match(m)]


def apply_sort(movies: list[dict], sort: str | None) -> list[dict]:
    """
    sort string examples:
    - rating_desc
    - rating_asc
    - popularity_desc
    - title_asc
    """
    if not sort:
        return movies

    key, _, direction = sort.partition("_")
    reverse = direction == "desc"

    if key == "rating":
        return sorted(movies, key=lambda m: m.get("vote_average") or 0, reverse=reverse)
    elif key == "popularity":
        return sorted(movies, key=lambda m: m.get("popularity") or 0, reverse=reverse)
    elif key == "title":
        return sorted(movies, key=lambda m: (m.get("title") or "").lower(), reverse=reverse)
    elif key == "year":
        return sorted(
            movies,
            key=lambda m: (m.get("release_date") or "")[:4],
            reverse=reverse,
        )
    return movies


def aggregate_movies(movies: list[dict], top_n: int = 5) -> dict:
    """
    Aggregation for /api/movies/summary:
    - total movies
    - overall average rating
    - group by genre (count, avg rating)
    - top N movies by rating
    """
    if not movies:
        return {
            "total_movies": 0,
            "overall_avg_rating": 0,
            "genres": [],
            "top_rated": [],
        }

    total_movies = len(movies)
    ratings = [m.get("vote_average") for m in movies if m.get("vote_average") is not None]

    overall_avg_rating = round(mean(ratings), 2) if ratings else 0

    # group by genre
    genre_buckets: dict[int, list[float]] = defaultdict(list)
    genre_counts: dict[int, int] = defaultdict(int)

    for m in movies:
        for gid in m.get("genre_ids", []):
            if m.get("vote_average") is not None:
                genre_buckets[gid].append(m["vote_average"])
            genre_counts[gid] += 1

    genres_summary = []
    for gid, count in genre_counts.items():
        genre_name = TMDB_GENRE_MAP.get(gid, f"Genre {gid}")
        avg_rating = round(mean(genre_buckets[gid]), 2) if genre_buckets[gid] else 0
        genres_summary.append(
            {
                "genre_id": gid,
                "genre_name": genre_name,
                "count": count,
                "avg_rating": avg_rating,
            }
        )

    # top N by rating
    movies_by_rating = sorted(
        movies, key=lambda m: m.get("vote_average") or 0, reverse=True
    )
    top_rated = [
        {
            "id": m["id"],
            "title": m["title"],
            "vote_average": m["vote_average"],
            "vote_count": m["vote_count"],
            "release_date": m["release_date"],
        }
        for m in movies_by_rating[:top_n]
    ]

    return {
        "total_movies": total_movies,
        "overall_avg_rating": overall_avg_rating,
        "genres": genres_summary,
        "top_rated": top_rated,
    }
