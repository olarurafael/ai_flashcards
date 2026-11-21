import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app import srs
from app.models import Card, Deck, Review
from app.quota import generations_left, start_of_day
from app.routers.decks import get_owned_card, get_owned_deck
from app.schemas import CardOut, ReviewIn, Stats
from app.security import AppSettings, CurrentUser, DbSession

router = APIRouter(tags=["study"])


@router.get("/study/due", response_model=list[CardOut])
def due_cards(
    db: DbSession,
    user: CurrentUser,
    deck_id: uuid.UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> list[Card]:
    query = (
        select(Card)
        .join(Deck)
        .where(Deck.user_id == user.id, Card.due_at <= datetime.now(UTC))
        .order_by(Card.due_at)
        .limit(limit)
    )
    if deck_id is not None:
        get_owned_deck(db, user, deck_id)
        query = query.where(Card.deck_id == deck_id)
    return list(db.scalars(query))


@router.post("/cards/{card_id}/review", response_model=CardOut)
def review_card(card_id: uuid.UUID, body: ReviewIn, db: DbSession, user: CurrentUser) -> Card:
    card = get_owned_card(db, user, card_id)
    now = datetime.now(UTC)
    try:
        schedule = srs.review(
            ease=card.ease,
            interval_days=card.interval_days,
            repetitions=card.repetitions,
            grade=body.grade,
            now=now,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    card.ease = schedule.ease
    card.interval_days = schedule.interval_days
    card.repetitions = schedule.repetitions
    card.due_at = schedule.due_at
    db.add(Review(card_id=card.id, user_id=user.id, grade=body.grade, reviewed_at=now))
    db.commit()
    return card


def _streak(review_days: set, today) -> int:
    """Consecutive days with at least one review, ending today or yesterday."""
    day = today if today in review_days else today - timedelta(days=1)
    streak = 0
    while day in review_days:
        streak += 1
        day -= timedelta(days=1)
    return streak


@router.get("/stats", response_model=Stats)
def stats(db: DbSession, user: CurrentUser, settings: AppSettings) -> Stats:
    now = datetime.now(UTC)
    total, due = db.execute(
        select(func.count(Card.id), func.count(Card.id).filter(Card.due_at <= now))
        .join(Deck)
        .where(Deck.user_id == user.id)
    ).one()

    review_times = db.scalars(
        select(Review.reviewed_at).where(
            Review.user_id == user.id, Review.reviewed_at >= now - timedelta(days=366)
        )
    ).all()
    today_start = start_of_day(now)
    review_days = {t.astimezone(UTC).date() for t in review_times}

    return Stats(
        total_cards=total,
        due_now=due,
        reviewed_today=sum(1 for t in review_times if t >= today_start),
        streak_days=_streak(review_days, now.date()),
        generations_left_today=generations_left(db, user, settings),
    )
