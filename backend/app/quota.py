from datetime import UTC, datetime, time

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Generation, User


def start_of_day(now: datetime) -> datetime:
    return datetime.combine(now.astimezone(UTC).date(), time(), tzinfo=UTC)


def generations_left(db: Session, user: User, settings: Settings) -> int:
    since = start_of_day(datetime.now(UTC))
    used = db.scalar(
        select(func.count())
        .select_from(Generation)
        .where(Generation.user_id == user.id, Generation.created_at >= since)
    )
    limit = settings.daily_generations_per_guest if user.is_guest else settings.daily_generations_per_user
    return max(0, limit - used)


def check_generation_quota(db: Session, user: User, settings: Settings) -> None:
    """Raise 429 when the user or the whole app is out of generations for today.

    The global cap is what bounds the OpenAI bill: anyone can create guest
    accounts, so per-user limits alone would not.
    """
    if generations_left(db, user, settings) == 0:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "You have used today's generations, try again tomorrow"
        )

    since = start_of_day(datetime.now(UTC))
    used_globally = db.scalar(
        select(func.count()).select_from(Generation).where(Generation.created_at >= since)
    )
    if used_globally >= settings.daily_generations_global:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "The demo is at today's usage limit, try again tomorrow"
        )
