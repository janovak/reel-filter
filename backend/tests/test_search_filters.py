"""
Tests for SearchFilters.has_content_filters — the Content Threshold rule
(see CONTEXT.md's "Content Threshold" entry, and plan
specs/002-filter-set-module/plan.md, B1).

The three Content Thresholds (sex_max, violence_max, language_max) behave as
a group: when any one of them is set, SearchService.search_movies switches
from a LEFT JOIN to an INNER JOIN against content_scores, so Movies with no
Content Score drop out of the results entirely. This rule now lives on
SearchFilters itself, as a derived member, rather than being recomputed
inline in the query builder.
"""
import pytest

from src.api.schemas.search import SearchFilters


def test_no_content_thresholds_set_is_inactive():
    """All three unset means content filtering is off."""
    filters = SearchFilters()
    assert filters.sex_max is None
    assert filters.violence_max is None
    assert filters.language_max is None
    assert filters.has_content_filters is False


@pytest.mark.parametrize("field", ["sex_max", "violence_max", "language_max"])
def test_any_one_content_threshold_set_is_active(field):
    """Any one Content Threshold set is enough to turn content filtering on."""
    filters = SearchFilters(**{field: 5})
    assert filters.has_content_filters is True


@pytest.mark.parametrize("field", ["sex_max", "violence_max", "language_max"])
def test_content_threshold_of_zero_counts_as_set(field):
    """
    sex_max=0 (etc.) means "none at all" — a real, active threshold — not
    "unset". This is the case a falsy check would get wrong.
    """
    filters = SearchFilters(**{field: 0})
    assert getattr(filters, field) == 0
    assert filters.has_content_filters is True


def test_all_three_content_thresholds_set_is_active():
    filters = SearchFilters(sex_max=0, violence_max=3, language_max=10)
    assert filters.has_content_filters is True


def test_content_thresholds_do_not_affect_other_members():
    """Setting a Content Threshold must not mark unrelated members active."""
    filters = SearchFilters(sex_max=0)
    assert filters.has_content_filters is True
    assert filters.imdb_min is None
    assert filters.genres is None
    assert filters.awards_min is None
