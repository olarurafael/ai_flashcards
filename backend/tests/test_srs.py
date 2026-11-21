from datetime import UTC, datetime, timedelta

import pytest

from app import srs

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def review(state: srs.Schedule | None, grade: int) -> srs.Schedule:
    if state is None:
        state = srs.Schedule(ease=2.5, interval_days=0, repetitions=0, due_at=NOW)
    return srs.review(
        ease=state.ease,
        interval_days=state.interval_days,
        repetitions=state.repetitions,
        grade=grade,
        now=NOW,
    )


def test_intervals_grow_one_six_then_by_ease():
    first = review(None, 4)
    second = review(first, 4)
    third = review(second, 4)
    assert [first.interval_days, second.interval_days, third.interval_days] == [1, 6, 15]
    assert third.due_at == NOW + timedelta(days=15)


def test_perfect_answer_raises_ease_and_good_keeps_it():
    assert review(None, 5).ease == pytest.approx(2.6)
    assert review(None, 4).ease == pytest.approx(2.5)


def test_lapse_resets_progress_and_returns_card_soon():
    learned = review(review(review(None, 4), 4), 4)
    lapsed = review(learned, 1)
    assert lapsed.repetitions == 0
    assert lapsed.interval_days == 0
    assert lapsed.due_at == NOW + srs.LAPSE_DELAY
    assert lapsed.ease < learned.ease


def test_ease_never_drops_below_minimum():
    state = None
    for _ in range(20):
        state = review(state, 0)
    assert state.ease == srs.MIN_EASE


@pytest.mark.parametrize("grade", [-1, 6])
def test_rejects_out_of_range_grades(grade):
    with pytest.raises(ValueError):
        review(None, grade)
