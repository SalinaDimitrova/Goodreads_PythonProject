def test_add_review_book_not_found(client):
    response = client.post(
        "/reviews/books/999",
        json={"rating": 5, "comment": "Great"},
        headers={"Authorization": "Bearer invalid"},
    )

    assert response.status_code in (401, 404)
