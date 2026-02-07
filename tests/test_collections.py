from tests_.test_books import create_user_and_login


def test_delete_default_collection_forbidden(client):
    token = create_user_and_login(client)

    # взимаме default колекциите
    collections = client.get(
        "/collections/",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    default = collections[0]

    response = client.delete(
        f"/collections/{default['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400

def test_add_and_remove_book_from_collection(client):
    token = create_user_and_login(client, role="author")

    genre = client.post(
        "/genres/",
        params={"name": "Sci-Fi"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    book = client.post(
        "/books/",
        json={
            "title": "Dune",
            "genre_ids": [genre["id"]],
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    collections = client.get(
        "/collections/",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    col_id = collections[0]["id"]

    response = client.post(
        f"/collections/{col_id}/books/{book['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    response = client.delete(
        f"/collections/{col_id}/books/{book['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

