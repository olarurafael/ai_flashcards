"""SM-2 spaced repetition, the algorithm behind SuperMemo 2 and early Anki.

Grades run 0-5. Anything below 3 is a lapse: the card starts over and comes
back within the same session instead of the next day.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

MIN_EASE = 1.3
LAPSE_DELAY = timedelta(minutes=10)


@dataclass(frozen=True)
class Schedule:
    ease: float
    interval_days: int
    repetitions: int
    due_at: datetime


def review(*, ease: float, interval_days: int, repetitions: int, grade: int, now: datetime) -> Schedule:
    if not 0 <= grade <= 5:
        raise ValueError(f"grade must be between 0 and 5, got {grade}")

    if grade < 3:
        repetitions = 0
        interval_days = 0
        due_at = now + LAPSE_DELAY
    else:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = round(interval_days * ease)
        repetitions += 1
        due_at = now + timedelta(days=interval_days)

    miss = 5 - grade
    ease = max(MIN_EASE, ease + 0.1 - miss * (0.08 + miss * 0.02))

    return Schedule(ease=round(ease, 4), interval_days=interval_days, repetitions=repetitions, due_at=due_at)
