import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, StringConstraints, model_validator

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Answer = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
DeckName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class Credentials(BaseModel):
    email: EmailStr
    # bcrypt only uses the first 72 bytes of a password.
    password: str = Field(min_length=8, max_length=64)


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None
    is_guest: bool


class DeckIn(BaseModel):
    name: DeckName


class DeckOut(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    card_count: int
    due_count: int


class CardIn(BaseModel):
    question: Question
    answer: Answer


class CardUpdate(BaseModel):
    question: Question | None = None
    answer: Answer | None = None


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    deck_id: uuid.UUID
    question: str
    answer: str
    interval_days: int
    repetitions: int
    due_at: datetime


class GenerateRequest(BaseModel):
    text: str | None = None
    url: HttpUrl | None = None

    @model_validator(mode="after")
    def exactly_one_source(self) -> "GenerateRequest":
        if (self.text is None) == (self.url is None):
            raise ValueError("Provide either text or url")
        if self.text is not None and not self.text.strip():
            raise ValueError("Text is empty")
        return self


class GenerateResult(BaseModel):
    created: list[CardOut]
    skipped_duplicates: int
    truncated: bool


class ReviewIn(BaseModel):
    grade: int = Field(ge=0, le=5)


class Stats(BaseModel):
    total_cards: int
    due_now: int
    reviewed_today: int
    streak_days: int
    generations_left_today: int
