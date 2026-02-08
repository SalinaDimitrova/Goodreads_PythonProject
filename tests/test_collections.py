from .test_books import create_user_and_login

def test_delete_default_collection_forbidden(client):
    headers = create_user_and_login(client)

    collections = client.get(
        "/collections/",
        headers=headers,
    ).json()

    default = collections[0]

    response = client.delete(
        f"/collections/{default['id']}",
        headers=headers,
    )

    assert response.status_code == 400

def test_add_and_remove_book_from_collection(client):
    headers = create_user_and_login(client, role="author")

    genre = client.post(
        "/genres/",
        params={"name": "Sci-Fi"},
        headers=headers,
    ).json()

    book = client.post(
        "/books/",
        json={
            "title": "Dune",
            "genre_ids": [genre["id"]],
        },
        headers=headers,
    ).json()

    collections = client.get(
        "/collections/",
        headers=headers,
    ).json()

    col_id = collections[0]["id"]

    response = client.post(
        f"/collections/{col_id}/books/{book['id']}",
        headers=headers,
    )
    assert response.status_code == 200

    response = client.delete(
        f"/collections/{col_id}/books/{book['id']}",
        headers=headers,
    )
    assert response.status_code == 200
