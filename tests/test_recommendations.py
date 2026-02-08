from .test_books import create_user_and_login

def test_recommendations_unauthorized(client):
    response = client.get("/recommendations/")
    assert response.status_code == 401

def test_recommendations_empty(client):
    headers = create_user_and_login(client)

    response = client.get(
        "/recommendations/",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []

def test_recommendations_with_data(client):
    headers = create_user_and_login(client, role="author")

    genre = client.post(
        "/genres/",
        params={"name": "Drama"},
        headers=headers,
    ).json()

    book = client.post(
        "/books/",
        json={"title": "Book", "genre_ids": [genre["id"]]},
        headers=headers,
    ).json()

    client.post(
        f"/reviews/books/{book['id']}",
        json={"rating": 5},
        headers=headers,
    )

    response = client.get(
        "/recommendations/",
        headers=headers,
    )

    assert response.status_code == 200
