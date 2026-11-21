from datetime import UTC, datetime, timedelta


def add_card(client, user, deck, question="Q", answer="A"):
    response = client.post(
        f"/api/decks/{deck['id']}/cards", json={"question": question, "answer": answer}, headers=user
    )
    return response.json()


def test_new_cards_are_due_and_reviewing_schedules_them(client, user, deck):
    card = add_card(client, user, deck)
    assert [c["id"] for c in client.get("/api/study/due", headers=user).json()] == [card["id"]]

    reviewed = client.post(f"/api/cards/{card['id']}/review", json={"grade": 4}, headers=user).json()
    assert reviewed["interval_days"] == 1
    assert reviewed["repetitions"] == 1
    due_at = datetime.fromisoformat(reviewed["due_at"])
    assert due_at - datetime.now(UTC) > timedelta(hours=23)

    assert client.get("/api/study/due", headers=user).json() == []


def test_due_queue_can_be_filtered_by_deck(client, user, deck):
    other = client.post("/api/decks", json={"name": "Other"}, headers=user).json()
    add_card(client, user, deck, "Q1")
    add_card(client, user, other, "Q2")

    due = client.get("/api/study/due", params={"deck_id": other["id"]}, headers=user).json()
    assert [c["question"] for c in due] == ["Q2"]


def test_invalid_grade_is_rejected(client, user, deck):
    card = add_card(client, user, deck)
    assert client.post(f"/api/cards/{card['id']}/review", json={"grade": 9}, headers=user).status_code == 422


def test_stats(client, user, deck):
    first = add_card(client, user, deck, "Q1")
    add_card(client, user, deck, "Q2")
    client.post(f"/api/cards/{first['id']}/review", json={"grade": 5}, headers=user)

    stats = client.get("/api/stats", headers=user).json()
    assert stats["total_cards"] == 2
    assert stats["due_now"] == 1
    assert stats["reviewed_today"] == 1
    assert stats["streak_days"] == 1
