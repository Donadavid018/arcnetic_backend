from django.urls import path
from .views import MoviesListView, MoviesSummaryView

urlpatterns = [
    path("movies/", MoviesListView.as_view(), name="movies-list"),
    path("movies/summary/", MoviesSummaryView.as_view(), name="movies-summary"),
]
