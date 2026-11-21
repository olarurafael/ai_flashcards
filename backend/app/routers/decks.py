import csv
import io
import json
import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.ingest import Document, IngestError, clean_text, extract_pdf_text, fetch_url_text
from app.llm import FlashcardGenerator, GenerationError, get_generator
from app.models import Card, Deck, Generation, User
from app.quota import check_generation_quota
from app.schemas import CardIn, CardOut, CardUpdate, DeckIn, DeckOut, GenerateRequest, GenerateResult
from app.security import AppSettings, CurrentUser, DbSession

router = APIRouter(tags=["decks"])

Generator = Annotated[FlashcardGenerator, Depends(get_generator)]


def get_owned_deck(db: Session, user: User, deck_id: uuid.UUID) -> Deck:
    deck = db.get(Deck, deck_id)
    # Someone else's deck gets the same 404 as a missing one, so ids can't be probed.
    if deck is None or deck.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deck not found")
    return deck


def get_owned_card(db: Session, user: User, card_id: uuid.UUID) -> Card:
    card = db.get(Card, card_id)
    if card is None or card.deck.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Card not found")
    return card


def _deck_rows(db: Session, user: User, deck_id: uuid.UUID | None = None) -> list[DeckOut]:
    now = datetime.now(UTC)
    query = (
        select(
            Deck,
            func.count(Card.id),
            func.count(case((Card.due_at <= now, Card.id))),
        )
        .outerjoin(Card)
        .where(Deck.user_id == user.id)
        .group_by(Deck.id)
        .order_by(Deck.created_at.desc())
    )
    if deck_id is not None:
        query = query.where(Deck.id == deck_id)
    return [
        DeckOut(id=deck.id, name=deck.name, created_at=deck.created_at, card_count=total, due_count=due)
        for deck, total, due in db.execute(query)
    ]


@router.get("/decks", response_model=list[DeckOut])
def list_decks(db: DbSession, user: CurrentUser) -> list[DeckOut]:
    return _deck_rows(db, user)


@router.post("/decks", response_model=DeckOut, status_code=status.HTTP_201_CREATED)
def create_deck(body: DeckIn, db: DbSession, user: CurrentUser) -> DeckOut:
    deck = Deck(user_id=user.id, name=body.name)
    db.add(deck)
    db.commit()
    return DeckOut(id=deck.id, name=deck.name, created_at=deck.created_at, card_count=0, due_count=0)


@router.get("/decks/{deck_id}", response_model=DeckOut)
def get_deck(deck_id: uuid.UUID, db: DbSession, user: CurrentUser) -> DeckOut:
    get_owned_deck(db, user, deck_id)
    return _deck_rows(db, user, deck_id)[0]


@router.patch("/decks/{deck_id}", response_model=DeckOut)
def rename_deck(deck_id: uuid.UUID, body: DeckIn, db: DbSession, user: CurrentUser) -> DeckOut:
    deck = get_owned_deck(db, user, deck_id)
    deck.name = body.name
    db.commit()
    return _deck_rows(db, user, deck_id)[0]


@router.delete("/decks/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(deck_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    db.delete(get_owned_deck(db, user, deck_id))
    db.commit()


@router.get("/decks/{deck_id}/cards", response_model=list[CardOut])
def list_cards(deck_id: uuid.UUID, db: DbSession, user: CurrentUser) -> list[Card]:
    get_owned_deck(db, user, deck_id)
    return list(db.scalars(select(Card).where(Card.deck_id == deck_id).order_by(Card.created_at)))


@router.post("/decks/{deck_id}/cards", response_model=CardOut, status_code=status.HTTP_201_CREATED)
def add_card(deck_id: uuid.UUID, body: CardIn, db: DbSession, user: CurrentUser) -> Card:
    get_owned_deck(db, user, deck_id)
    card = Card(deck_id=deck_id, question=body.question, answer=body.answer)
    db.add(card)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This deck already has that question") from None
    return card


@router.patch("/cards/{card_id}", response_model=CardOut)
def update_card(card_id: uuid.UUID, body: CardUpdate, db: DbSession, user: CurrentUser) -> Card:
    card = get_owned_card(db, user, card_id)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(card, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This deck already has that question") from None
    return card


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    db.delete(get_owned_card(db, user, card_id))
    db.commit()


def _generate_into_deck(
    *,
    db: Session,
    user: User,
    deck: Deck,
    document: Document,
    source: str,
    generator: FlashcardGenerator,
    settings: Settings,
) -> GenerateResult:
    try:
        generated = generator.generate(document.text, settings.max_cards_per_generation)
    except GenerationError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    existing = set(db.scalars(select(Card.question).where(Card.deck_id == deck.id)))
    created: list[Card] = []
    skipped = 0
    for item in generated:
        question = item.question.strip()[:500]
        answer = item.answer.strip()[:2000]
        if not question or not answer:
            continue
        if question in existing:
            skipped += 1
            continue
        existing.add(question)
        created.append(Card(deck_id=deck.id, question=question, answer=answer))

    db.add_all(created)
    db.add(
        Generation(user_id=user.id, source=source, input_chars=len(document.text), cards_created=len(created))
    )
    db.commit()
    return GenerateResult(
        created=[CardOut.model_validate(card) for card in created],
        skipped_duplicates=skipped,
        truncated=document.truncated,
    )


@router.post("/decks/{deck_id}/generate", response_model=GenerateResult)
def generate_from_text_or_url(
    deck_id: uuid.UUID,
    body: GenerateRequest,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    generator: Generator,
) -> GenerateResult:
    deck = get_owned_deck(db, user, deck_id)
    check_generation_quota(db, user, settings)
    try:
        if body.url is not None:
            document = fetch_url_text(str(body.url), settings.max_input_chars)
            source = "url"
        else:
            document = clean_text(body.text, settings.max_input_chars)
            source = "text"
    except IngestError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    return _generate_into_deck(
        db=db, user=user, deck=deck, document=document, source=source, generator=generator, settings=settings
    )


@router.post("/decks/{deck_id}/generate/pdf", response_model=GenerateResult)
def generate_from_pdf(
    deck_id: uuid.UUID,
    file: Annotated[UploadFile, File()],
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    generator: Generator,
) -> GenerateResult:
    deck = get_owned_deck(db, user, deck_id)
    check_generation_quota(db, user, settings)
    data = file.file.read(settings.max_pdf_bytes + 1)
    if len(data) > settings.max_pdf_bytes:
        limit_mb = settings.max_pdf_bytes // (1024 * 1024)
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"PDFs are limited to {limit_mb} MB")
    try:
        document = extract_pdf_text(data, settings.max_input_chars)
    except IngestError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    return _generate_into_deck(
        db=db, user=user, deck=deck, document=document, source="pdf", generator=generator, settings=settings
    )


@router.get("/decks/{deck_id}/export")
def export_deck(
    deck_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    format: Literal["csv", "json", "anki"] = "csv",
) -> Response:
    deck = get_owned_deck(db, user, deck_id)
    cards = db.scalars(select(Card).where(Card.deck_id == deck_id).order_by(Card.created_at)).all()

    if format == "json":
        body = json.dumps([{"question": c.question, "answer": c.answer} for c in cards], indent=2)
        media_type, extension = "application/json", "json"
    else:
        buffer = io.StringIO()
        if format == "anki":
            # Header lines Anki 2.1.55+ reads to import without asking about columns.
            buffer.write("#separator:tab\n#html:false\n")
            writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
        else:
            writer = csv.writer(buffer, lineterminator="\n")
            writer.writerow(["question", "answer"])
        writer.writerows([c.question, c.answer] for c in cards)
        body = buffer.getvalue()
        media_type, extension = ("text/plain", "txt") if format == "anki" else ("text/csv", "csv")

    filename = "".join(ch if ch.isalnum() else "_" for ch in deck.name).strip("_") or "deck"
    return Response(
        body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}.{extension}"'},
    )
