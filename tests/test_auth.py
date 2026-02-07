def test_login_invalid_credentials(client):
    response = client.post(
        "/login",
        data={"username": "nope", "password": "wrong"},
    )
    assert response.status_code == 401

def test_login_success(client):
    client.post(
        "/users/",
        json={
            "username": "user1",
            "password": "secret123",
            "role": "user",
        },
    )

    response = client.post(
        "/login",
        data={"username": "user1", "password": "secret123"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
