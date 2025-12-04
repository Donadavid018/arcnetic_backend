from rest_framework import serializers
from .utils import TMDB_GENRE_MAP


class MovieSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    overview = serializers.CharField(allow_blank=True, allow_null=True)
    release_date = serializers.CharField(allow_blank=True, allow_null=True)
    original_language = serializers.CharField()
    vote_average = serializers.FloatField()
    vote_count = serializers.IntegerField()
    popularity = serializers.FloatField()
    genre_ids = serializers.ListField(child=serializers.IntegerField())
    poster_path = serializers.CharField(allow_blank=True, allow_null=True)

    genres = serializers.SerializerMethodField()

    def get_genres(self, obj):
        return [TMDB_GENRE_MAP.get(gid, f"Genre {gid}") for gid in obj.get("genre_ids", [])]


class GenreSummarySerializer(serializers.Serializer):
    genre_id = serializers.IntegerField()
    genre_name = serializers.CharField()
    count = serializers.IntegerField()
    avg_rating = serializers.FloatField()


class MoviesSummarySerializer(serializers.Serializer):
    total_movies = serializers.IntegerField()
    overall_avg_rating = serializers.FloatField()
    genres = GenreSummarySerializer(many=True)
    top_rated = serializers.ListField()
