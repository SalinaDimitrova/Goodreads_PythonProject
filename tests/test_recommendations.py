from tests_.test_books import create_user_and_login


def test_recommendations_unauthorized(client):
    response = client.get("/recommendations/")
    assert response.status_code == 401

def test_recommendations_empty(client):
    token = create_user_and_login(client)

    response = client.get(
        "/recommendations/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_recommendations_with_data(client):
    token = create_user_and_login(client, role="author")

    genre = client.post(
        "/genres/",
        params={"name": "Drama"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    book = client.post(
        "/books/",
        json={"title": "Book", "genre_ids": [genre["id"]]},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    client.post(
        f"/reviews/books/{book['id']}",
        json={"rating": 5},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/recommendations/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1
