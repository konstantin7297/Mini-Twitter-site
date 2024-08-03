import os
from typing import List, Any

from typing_extensions import Annotated
from sqlalchemy import ForeignKey, Column, Table, Integer, Result, select, insert, Row, \
    create_engine, Select, Insert
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship, \
    MappedAsDataclass, sessionmaker


def get_db_url() -> str:
    if os.environ.get("ENV"):
        return "postgresql+psycopg2://admin:admin@localhost:5432/db"
    return "postgresql+psycopg2://admin:admin@postgres:5432/db"


DATABASE_URL: str = get_db_url()

engine = create_engine(DATABASE_URL)
session_obj = sessionmaker(bind=engine, expire_on_commit=False)
session = session_obj()

str_u = Annotated[str, mapped_column(unique=True)]
int_apk = Annotated[int, mapped_column(autoincrement=True, primary_key=True)]
user_fk = Annotated[int, mapped_column(ForeignKey(
    "users.id", ondelete="CASCADE"
), nullable=False)]
tweet_fkn = Annotated[int, mapped_column(ForeignKey(
    "tweets.id", ondelete="CASCADE"
), nullable=True)]


class Base(MappedAsDataclass, DeclarativeBase):
    id: Mapped[int_apk] = mapped_column(init=False)


like = Table(
        "likes",
        Base.metadata,
        Column("user_id", ForeignKey(
            "users.id", ondelete="CASCADE"
        ), primary_key=True),
        Column("tweet_id", ForeignKey(
            "tweets.id", ondelete="CASCADE"
        ), primary_key=True),
    )

follow = Table(
        "follows",
        Base.metadata,
        Column("following", Integer, ForeignKey(
            "users.id", ondelete="CASCADE"
        ), primary_key=True),
        Column("follower", Integer, ForeignKey(
            "users.id", ondelete="CASCADE"
        ), primary_key=True),
    )


class User(Base):
    __tablename__ = "users"
    api_key: Mapped[str_u]
    name: Mapped[str]
    tweets: Mapped[List["Tweet"]] = relationship(
        "Tweet",
        backref="user", uselist=True, cascade="delete", lazy="selectin"
    )
    user_likes: Mapped[List["Tweet"]] = relationship(
        secondary=like, back_populates="tweet_likes", uselist=True, lazy="selectin",
        cascade="save-update"
    )
    following: Mapped[List["User"]] = relationship(
        "User",
        secondary="follows",
        primaryjoin="User.id == follows.c.following",
        secondaryjoin="User.id == follows.c.follower",
        back_populates="follower",
        cascade="save-update",
        lazy="immediate",
        uselist=True,
    )
    follower: Mapped[List["User"]] = relationship(
        "User",
        secondary="follows",
        primaryjoin="User.id == follows.c.follower",
        secondaryjoin="User.id == follows.c.following",
        back_populates="following",
        cascade="save-update",
        lazy="immediate",
        uselist=True,
    )

    @staticmethod
    def get_user(api_key: str = None, user_id: int = None) -> Row[Any] | bool:  # type: ignore

        if api_key:
            cmd: Select = select(User).where(User.api_key == api_key)  # type: ignore
        elif user_id:
            cmd: Select = select(User).where(User.id == user_id)  # type: ignore
        else:
            return False

        result: Result = session.execute(cmd)
        user: Row[Any] | None = result.fetchone()

        if user:
            return user[0]
        else:
            return False

    @staticmethod
    def add_like(user, tweet_id: int) -> bool:
        to_tweet: Row[Any] | bool = Tweet.get_tweet(tweet_id)
        if to_tweet and not to_tweet.user_id == user.id:  # type: ignore
            user.user_likes.append(to_tweet)
            session.commit()
            return True
        else:
            return False

    @staticmethod
    def remove_like(user, tweet_id: int) -> bool:
        to_tweet: Row[Any] | bool = Tweet.get_tweet(tweet_id)
        if to_tweet:
            user.user_likes.remove(to_tweet)
            session.commit()
            return True
        else:
            return False

    @staticmethod
    def add_following(user, user_id: int) -> bool:
        follow_to: Result = session.execute(
            select(User).where(User.id == user_id)  # type: ignore
        )
        following: Row[Any] | None = follow_to.fetchone()

        if following:
            user.following.append(following[0])
            session.commit()
            return True
        else:
            return False

    @staticmethod
    def remove_following(user, user_id: int) -> bool:
        follow_to: Result = session.execute(
            select(User).where(User.id == user_id)  # type: ignore
        )
        user_to: Row[Any] | None = follow_to.fetchone()

        if user_to:
            user.following.remove(user_to[0])
            session.commit()
            return True
        else:
            return False


class Tweet(Base):
    __tablename__ = "tweets"
    tweet_data: Mapped[str]
    user_id: Mapped[user_fk]
    tweet_likes: Mapped[List["User"]] = relationship(
        secondary=like, back_populates="user_likes", uselist=True, lazy="selectin",
        cascade="delete"
    )
    medias: Mapped[List["Media"]] = relationship(
        "Media",
        backref="tweet", uselist=True, cascade="delete", lazy="selectin"
    )

    @staticmethod
    def add(user: User, data: str, medias: List[int]) -> Row[Any] | bool:
        cmd: Insert = insert(Tweet).returning(Tweet.id).values(
            tweet_data=data, user_id=user.id
        )
        result: Result = session.execute(cmd)
        tweet_id: Row[Any] | None = result.fetchone()

        if tweet_id:
            for media_id in medias:
                media: Any = Media.get(media_id)

                if media:
                    media.tweet_id = tweet_id[0]

            session.commit()
            return tweet_id[0]
        else:
            return False

    @staticmethod
    def get_tweet(tweet_id: int) -> Row[Any] | bool:
        cmd: Select = select(Tweet).where(Tweet.id == tweet_id)  # type: ignore
        result: Result = session.execute(cmd)
        tweet: Row[Any] | None = result.fetchone()

        if tweet:
            return tweet[0]
        else:
            return False

    @staticmethod
    def delete(user: User, tweet_id: int) -> bool:
        to_tweet: Row[Any] | bool = Tweet.get_tweet(tweet_id)

        if to_tweet and to_tweet in user.tweets:
            session.delete(to_tweet)
            session.commit()
            return True

        else:
            return False


class Media(Base):
    __tablename__ = "medias"
    filename: Mapped[str_u]
    tweet_id: Mapped[tweet_fkn]

    @staticmethod
    def add(filename: str) -> Row[Any] | bool:
        cmd: Insert = insert(Media).returning(Media.id).values(filename=filename)

        try:
            result: Result = session.execute(cmd)
            media_id: Row[Any] | None = result.fetchone()
        except Exception:
            media_id = None
            session.rollback()

        if media_id:
            session.commit()
            return media_id[0]
        else:
            return False

    @staticmethod
    def get(media_id: int) -> Row[Any] | bool:
        cmd: Select = select(Media).where(Media.id == media_id)  # type: ignore
        result: Result = session.execute(cmd)
        media: Row[Any] | None = result.fetchone()

        if media:
            return media[0]
        else:
            return False


def creates():
    Base.metadata.create_all(checkfirst=True, bind=engine)
    session.execute(insert(User).values(api_key="test", name="user1"))
    session.execute(insert(User).values(api_key="test2", name="user2"))
    session.commit()
