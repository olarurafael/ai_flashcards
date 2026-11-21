from conftest import auth_headers


def test_register_then_login(client):
    auth_headers(client, "Grace@Example.com")
    response = client.post(
        "/api/auth/login", json={"email": "grace@example.com", "password": "correct-horse"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "grace@example.com"
    assert me.json()["is_guest"] is False


def test_duplicate_email_is_rejected(client):
    auth_headers(client)
    response = client.post(
        "/api/auth/register", json={"email": "ada@example.com", "password": "another-pass"}
    )
    assert response.status_code == 409


def test_wrong_password_is_rejected(client):
    auth_headers(client)
    response = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "wrong-horse"})
    assert response.status_code == 401


def test_short_password_is_rejected(client):
    response = client.post("/api/auth/register", json={"email": "ada@example.com", "password": "short"})
    assert response.status_code == 422


def test_guest_account(client):
    token = client.post("/api/auth/guest").json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["is_guest"] is True
    assert me.json()["email"] is None


def test_guest_can_claim_an_account_and_keep_decks(client):
    token = client.post("/api/auth/guest").json()["access_token"]
    guest = {"Authorization": f"Bearer {token}"}
    client.post("/api/decks", json={"name": "Kept"}, headers=guest)

    claimed = client.post(
        "/api/auth/claim", json={"email": "new@example.com", "password": "correct-horse"}, headers=guest
    )
    assert claimed.status_code == 200

    login = client.post("/api/auth/login", json={"email": "new@example.com", "password": "correct-horse"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert [d["name"] for d in client.get("/api/decks", headers=headers).json()] == ["Kept"]
    assert client.get("/api/auth/me", headers=headers).json()["is_guest"] is False


def test_claim_is_only_for_guests(client, user):
    response = client.post(
        "/api/auth/claim", json={"email": "other@example.com", "password": "correct-horse"}, headers=user
    )
    assert response.status_code == 400


def test_requests_without_valid_token_are_rejected(client):
    assert client.get("/api/decks").status_code == 401
    assert client.get("/api/decks", headers={"Authorization": "Bearer nonsense"}).status_code == 401
