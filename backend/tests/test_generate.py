from app.config import get_settings
from app.llm import GeneratedCard


def generate(client, user, deck, **body):
    return client.post(f"/api/decks/{deck['id']}/generate", json=body, headers=user)


def test_generates_cards_from_text(client, user, deck, generator):
    response = generate(client, user, deck, text="France is a country. Its capital is Paris.")
    assert response.status_code == 200
    result = response.json()
    assert [c["question"] for c in result["created"]] == [
        "What is the capital of France?",
        "What is 2 + 2?",
    ]
    assert result["skipped_duplicates"] == 0
    assert result["truncated"] is False
    assert len(client.get(f"/api/decks/{deck['id']}/cards", headers=user).json()) == 2


def test_skips_duplicates_within_a_deck(client, user, deck, generator):
    generate(client, user, deck, text="first")
    generator.cards = [
        GeneratedCard(question="What is 2 + 2?", answer="four"),
        GeneratedCard(question="New question?", answer="New answer"),
    ]
    result = generate(client, user, deck, text="second").json()
    assert [c["question"] for c in result["created"]] == ["New question?"]
    assert result["skipped_duplicates"] == 1


def test_long_input_is_truncated(client, user, deck, generator):
    limit = get_settings().max_input_chars
    result = generate(client, user, deck, text="word " * limit).json()
    assert result["truncated"] is True
    assert len(generator.calls[0]) == limit


def test_requires_exactly_one_source(client, user, deck, generator):
    assert generate(client, user, deck).status_code == 422
    assert generate(client, user, deck, text="x", url="https://example.com").status_code == 422
    assert generate(client, user, deck, text="   ").status_code == 422


def test_rejects_private_urls_before_fetching(client, user, deck, generator):
    response = generate(client, user, deck, url="http://127.0.0.1:8000/api/health")
    assert response.status_code == 422
    assert generator.calls == []


def test_model_failure_returns_502_and_saves_nothing(client, user, deck, generator):
    generator.error = "The flashcard model is unavailable, try again later"
    response = generate(client, user, deck, text="anything")
    assert response.status_code == 502
    assert client.get(f"/api/decks/{deck['id']}/cards", headers=user).json() == []


def test_daily_quota(client, deck, generator, user):
    limit = get_settings().daily_generations_per_user
    for _ in range(limit):
        assert generate(client, user, deck, text="text").status_code == 200
    assert generate(client, user, deck, text="text").status_code == 429
    assert client.get("/api/stats", headers=user).json()["generations_left_today"] == 0


def test_guests_get_a_smaller_quota(client, generator):
    token = client.post("/api/auth/guest").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    deck = client.post("/api/decks", json={"name": "Guest deck"}, headers=headers).json()
    for _ in range(get_settings().daily_generations_per_guest):
        assert generate(client, headers, deck, text="text").status_code == 200
    assert generate(client, headers, deck, text="text").status_code == 429


def test_pdf_upload_rejects_non_pdf(client, user, deck, generator):
    response = client.post(
        f"/api/decks/{deck['id']}/generate/pdf",
        files={"file": ("notes.pdf", b"not really a pdf", "application/pdf")},
        headers=user,
    )
    assert response.status_code == 422
    assert generator.calls == []
