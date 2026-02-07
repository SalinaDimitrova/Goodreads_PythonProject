def test_create_user(client):
    response = client.post(
        "/users/",
        json={
            "username": "testuser",
            "password": "secret123",
            "role": "user",
        },
    )

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data
