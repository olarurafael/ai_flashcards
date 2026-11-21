from conftest import auth_headers


def test_create_list_rename_delete(client, user):
    created = client.post("/api/decks", json={"name": "  Biology  "}, headers=user).json()
    assert created["name"] == "Biology"

    assert [d["name"] for d in client.get("/api/decks", headers=user).json()] == ["Biology"]

    renamed = client.patch(f"/api/decks/{created['id']}", json={"name": "Cell biology"}, headers=user)
    assert renamed.json()["name"] == "Cell biology"

    assert client.delete(f"/api/decks/{created['id']}", headers=user).status_code == 204
    assert client.get("/api/decks", headers=user).json() == []


def test_decks_are_private(client, user, deck):
    other = auth_headers(client, "eve@example.com")
    assert client.get(f"/api/decks/{deck['id']}", headers=other).status_code == 404
    assert client.get(f"/api/decks/{deck['id']}/cards", headers=other).status_code == 404
    assert client.get("/api/decks", headers=other).json() == []

    card = client.post(
        f"/api/decks/{deck['id']}/cards", json={"question": "Q", "answer": "A"}, headers=user
    ).json()
    assert client.delete(f"/api/cards/{card['id']}", headers=other).status_code == 404
    assert client.post(f"/api/cards/{card['id']}/review", json={"grade": 4}, headers=other).status_code == 404


def test_manual_cards_and_duplicates(client, user, deck):
    url = f"/api/decks/{deck['id']}/cards"
    assert client.post(url, json={"question": "Q1", "answer": "A1"}, headers=user).status_code == 201
    assert client.post(url, json={"question": "Q1", "answer": "other"}, headers=user).status_code == 409

    card_id = client.get(url, headers=user).json()[0]["id"]
    updated = client.patch(f"/api/cards/{card_id}", json={"answer": "A1, edited"}, headers=user)
    assert updated.json()["answer"] == "A1, edited"

    summary = client.get(f"/api/decks/{deck['id']}", headers=user).json()
    assert summary["card_count"] == 1
    assert summary["due_count"] == 1


def test_export_formats(client, user, deck):
    client.post(
        f"/api/decks/{deck['id']}/cards", json={"question": 'Say "hi"', "answer": "a, b"}, headers=user
    )
    base = f"/api/decks/{deck['id']}/export"

    csv = client.get(base, params={"format": "csv"}, headers=user)
    assert csv.text == 'question,answer\n"Say ""hi""","a, b"\n'
    assert 'filename="Geography.csv"' in csv.headers["content-disposition"]

    anki = client.get(base, params={"format": "anki"}, headers=user)
    assert anki.text.startswith("#separator:tab\n#html:false\n")

    as_json = client.get(base, params={"format": "json"}, headers=user)
    assert as_json.json() == [{"question": 'Say "hi"', "answer": "a, b"}]
