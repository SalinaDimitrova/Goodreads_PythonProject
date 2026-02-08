def create_user_and_login(client, role="author"):
    client.post(
        "/users/",
        json={
            "username": "author",
            "password": "secret123",
            "role": role,
        },
    )

    res = client.post(
        "/login",
        data={"username": "author", "password": "secret123"},
    )

    access_token = res.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

def test_create_book_forbidden(client):
    headers = create_user_and_login(client, role="user")

    response = client.post(
        "/books/",
        json={"title": "Book", "genre_ids": [1]},
        headers=headers,
    )

    assert response.status_code == 403

def test_create_book_without_genre(client):
    headers = create_user_and_login(client, role="author")

    response = client.post(
        "/books/",
        json={
            "title": "Book without genre",
            "description": "test",
            "genre_ids": [],
        },
        headers=headers,
    )

    assert response.status_code == 400

def test_create_book_success(client):
    headers = create_user_and_login(client, role="author")

    genre = client.post(
        "/genres/",
        params={"name": "Fantasy"},
        headers=headers,
    ).json()

    response = client.post(
        "/books/",
        json={
            "title": "Valid Book",
            "description": "Nice",
            "genre_ids": [genre["id"]],
        },
        headers=headers,
    )

    assert response.status_code == 200

def test_create_and_get_book(client):
    headers = create_user_and_login(client, role="author")

    genre = client.post(
        "/genres/",
        params={"name": "Fantasy"},
        headers=headers,
    ).json()

    response = client.post(
        "/books/",
        json={
            "title": "My Book",
            "description": "Nice",
            "genre_ids": [genre["id"]],
        },
        headers = headers,
    )

    assert response.status_code == 200
    book_id = response.json()["id"]

    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
