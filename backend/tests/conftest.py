import os

# Must be set before the app reads its settings.
os.environ.setdefault(
    "DATABASE_URL",
    os.getenv("TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/flashcards_test"),
)
os.environ.setdefault("JWT_SECRET", "test-secret-that-is-long-enough-for-hs256")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import Base, get_engine
from app.llm import GeneratedCard, GenerationError, get_generator
from app.main import app


class FakeGenerator:
    """Stands in for OpenAI; tests set `cards` or `error` before generating."""

    def __init__(self) -> None:
        self.cards = [
            GeneratedCard(question="What is the capital of France?", answer="Paris"),
            GeneratedCard(question="What is 2 + 2?", answer="4"),
        ]
        self.error: str | None = None
        self.calls: list[str] = []

    def generate(self, text: str, max_cards: int) -> list[GeneratedCard]:
        self.calls.append(text)
        if self.error:
            raise GenerationError(self.error)
        return self.cards[:max_cards]


@pytest.fixture(scope="session", autouse=True)
def schema():
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with get_engine().begin() as conn:
        conn.execute(text(f"TRUNCATE {names} CASCADE"))


@pytest.fixture
def generator():
    fake = FakeGenerator()
    app.dependency_overrides[get_generator] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_generator, None)


@pytest.fixture
def client():
    return TestClient(app)


def auth_headers(client: TestClient, email: str = "ada@example.com") -> dict[str, str]:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def user(client):
    return auth_headers(client)


@pytest.fixture
def deck(client, user):
    response = client.post("/api/decks", json={"name": "Geography"}, headers=user)
    assert response.status_code == 201
    return response.json()
