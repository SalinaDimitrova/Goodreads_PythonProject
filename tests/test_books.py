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
    return res.json()["access_token"]


def test_create_book_forbidden(client):
    token = create_user_and_login(client, role="user")

    response = client.post(
        "/books/",
        json={"title": "Book", "genre_ids": [1]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

def test_create_book_without_genre(client):
    token = create_user_and_login(client, role="author")

    response = client.post(
        "/books/",
        json={
            "title": "Book without genre",
            "description": "test",
            "genre_ids": [],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400

def test_create_book_success(client):
    token = create_user_and_login(client, role="author")

    # create genre
    genre = client.post(
        "/genres/",
        params={"name": "Fantasy"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    response = client.post(
        "/books/",
        json={
            "title": "Valid Book",
            "description": "Nice",
            "genre_ids": [genre["id"]],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Valid Book"

def test_create_and_get_book(client):
    token = create_user_and_login(client, role="author")

    # create genre
    genre = client.post(
        "/genres/",
        params={"name": "Fantasy"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    # create book
    response = client.post(
        "/books/",
        json={
            "title": "My Book",
            "description": "Nice",
            "genre_ids": [genre["id"]],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    book_id = response.json()["id"]

    # get book
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
