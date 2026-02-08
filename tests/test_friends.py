from .test_books import create_user_and_login

def test_add_self_as_friend(client):
    headers = create_user_and_login(client)

    response = client.post(
        "/friends/1",
        headers=headers,
    )

    assert response.status_code == 400

def test_friend_flow(client):
    # user1
    client.post("/users/", json={
        "username": "u1", "password": "pass123", "role": "user"
    })
    token1 = client.post("/login", data={
        "username": "u1", "password": "pass123"
    }).json()["access_token"]

    # user2
    client.post("/users/", json={
        "username": "u2", "password": "pass123", "role": "user"
    })
    token2 = client.post("/login", data={
        "username": "u2", "password": "pass123"
    }).json()["access_token"]

    fr = client.post(
        "/friends/2",
        headers={"Authorization": f"Bearer {token1}"},
    ).json()

    response = client.post(
        f"/friends/requests/{fr['id']}/accept",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 200

    response = client.get(
        "/friends/",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert response.status_code == 200
