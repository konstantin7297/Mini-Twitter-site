import os

from sqlalchemy import Row

os.environ["ENV"] = "TEST"

import pytest

from ..routes import app
from ..models import session, User


@pytest.fixture(scope='session')
def application():
    for num in range(1, 3):
        session.add(User(
            api_key=f"test{num}",  # type: ignore
            name=f"name{num}",
            follower=[],
            following=[],
            tweets=[],
            user_likes=[]
        ))
    session.commit()

    _app = app
    _app.config["TESTING"] = True
    yield _app.test_client()

    session.query(User).filter(User.api_key == "test1").delete()
    session.query(User).filter(User.api_key == "test2").delete()
    session.commit()


@pytest.fixture
def create_tweet(application):
    return application.post(
        "/api/tweets",
        headers={"api-key": "test1"},
        json={"tweet_data": "test_tweet", "tweet_media_ids": []}
    ).json.get("tweet_id")


@pytest.fixture
def get_user():
    user: Row[tuple[int]] | None = session.query(User.id).filter(
        User.api_key == "test1"
    ).first()
    if user:
        return user[0]
