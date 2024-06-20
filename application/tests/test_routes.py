def test_tweets(application):
    response1 = application.get("/api/tweets", headers={"api-key": "test1"})
    response2 = application.post(
        "/api/tweets",
        headers={"api-key": "test1"},
        json={"tweet_data": "test_tweet", "tweet_media_ids": []}
    )
    assert response1.status_code == 200
    assert response2.status_code == 201


def test_medias(application):
    response = application.post(
        "/api/medias",
        headers={"api-key": "test1"},
        data={'file': (open('tests/image.jpg', "rb"), './tests/image.jpg')},
        content_type='multipart/form-data'
    )
    assert response.status_code == 201


def test_delete_tweet(application, create_tweet):
    response = application.delete(
        f"/api/tweets/{create_tweet}",
        headers={"api-key": "test1"}
    )
    assert response.status_code == 200


def test_like_tweet(application, create_tweet):
    response1 = application.post(
        f"/api/tweets/{create_tweet}/likes",
        headers={"api-key": "test2"}
    )
    response2 = application.delete(
        f"/api/tweets/{create_tweet}/likes",
        headers={"api-key": "test2"}
    )
    assert response1.status_code == 200
    assert response2.status_code == 200


def test_follow(application, get_user):
    response1 = application.post(
        f"/api/users/{get_user}/follow",
        headers={"api-key": "test2"}
    )
    response2 = application.delete(
        f"/api/users/{get_user}/follow",
        headers={"api-key": "test2"}
    )
    assert response1.status_code == 200
    assert response2.status_code == 200


def test_me(application, get_user):
    response1 = application.get(
        "/api/users/me", headers={"api-key": "test1"}
    )
    response2 = application.get(
        f"/api/users/{get_user}", headers={"api-key": "test1"}
    )
    assert response1.status_code == 200
    assert response2.status_code == 200
