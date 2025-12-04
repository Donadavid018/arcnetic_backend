from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage

from .services import fetch_movies_from_tmdb, TMDBApiError
from .serializers import MovieSerializer, MoviesSummarySerializer
from .utils import parse_filter_query, apply_filters, apply_sort, aggregate_movies


class MoviesListView(APIView):
    """
    GET /api/movies/?page=1&limit=20&sort=rating_desc&filter=year:2023,genre:Action

    Supports:
    - Pagination: page, limit
    - Sorting: rating_asc, rating_desc, popularity_desc, title_asc, year_desc, ...
    - Filtering: year, language, min_rating, genre
    """

    def get(self, request):
        try:
            page = int(request.GET.get("page", 1))
        except ValueError:
            return Response(
                {"detail": "Invalid 'page' parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            limit = int(request.GET.get("limit", 20))
        except ValueError:
            return Response(
                {"detail": "Invalid 'limit' parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sort = request.GET.get("sort")
        filter_str = request.GET.get("filter")

        try:
            raw_movies = fetch_movies_from_tmdb(page=page)
        except TMDBApiError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Note: TMDB already paginates, but we also paginate in our API for consistency.
        filters = parse_filter_query(filter_str)
        filtered = apply_filters(raw_movies, filters)
        sorted_movies = apply_sort(filtered, sort)

        paginator = Paginator(sorted_movies, limit)
        try:
            page_obj = paginator.page(1)  # our dataset already corresponds to TMDB page
        except EmptyPage:
            page_obj = []

        serializer = MovieSerializer(page_obj, many=True)

        return Response(
            {
                "page": page,
                "limit": limit,
                "total_items": len(sorted_movies),
                "results": serializer.data,
            }
        )


class MoviesSummaryView(APIView):
    """
    GET /api/movies/summary/?page=1&filter=year:2023,language:en

    Uses the same data source but returns aggregated information:
    - total movies
    - overall average rating
    - per-genre stats
    - top rated movies
    """

    def get(self, request):
        try:
            page = int(request.GET.get("page", 1))
        except ValueError:
            return Response(
                {"detail": "Invalid 'page' parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filter_str = request.GET.get("filter")
        sort = request.GET.get("sort")  # optional, can reuse same sort logic

        try:
            raw_movies = fetch_movies_from_tmdb(page=page)
        except TMDBApiError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        filters = parse_filter_query(filter_str)
        filtered = apply_filters(raw_movies, filters)
        sorted_movies = apply_sort(filtered, sort)

        summary = aggregate_movies(sorted_movies, top_n=5)
        serializer = MoviesSummarySerializer(summary)

        return Response(serializer.data)


# Create your views here.
