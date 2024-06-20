import os
from typing import Any, Dict

from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import Flask, request, jsonify
from werkzeug.exceptions import MethodNotAllowed, Unauthorized
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename
from flasgger import Swagger, APISpec, swag_from  # type: ignore

from .models import User, Tweet, Media  # type: ignore
from .schemas import TweetsPostForm, MediasPostForm, IdForm  # type: ignore


app: Flask = Flask(__name__)
app.config["WTF_CSRF_ENABLED"] = False
app.config['UPLOAD_FOLDER'] = os.path.dirname(__file__) + "/images/"
file_count: int = len(os.listdir(app.config['UPLOAD_FOLDER']))

spec: APISpec = APISpec(
    title='Twitter',
    version='1.0.0',
    openapi_version='2.0',
    plugins=[
        FlaskPlugin(),
        MarshmallowPlugin()
    ]
)

template: Dict = spec.to_flasgger(app, definitions=[TweetsPostForm, MediasPostForm, IdForm])
swagger: Swagger = Swagger(app, template=template)


@app.before_request
def authorization():
    if request.path in [
        "/api/tweets",
        "/api/medias",
        "/api/tweets/<int:tweet_id>",
        "/api/tweets/<int:tweet_id>/likes",
        "/api/users/<int:user_id>/follow",
        "/api/users/me",
        "/api/users/<int:user_id>",
    ]:
        response: Any = User.get_user(api_key=request.headers.get("api-key"))

        if not response:
            return jsonify({
                "result": False,
                "error_type": Unauthorized().name,
                "error_message": Unauthorized().description
            }), 401


@app.route("/api/tweets", methods=["GET", "POST"])
@swag_from("./docs/tweets_post.yml", methods=["POST"])
@swag_from("./docs/tweets_get.yml", methods=["GET"])
def tweets():
    user: Any = User.get_user(api_key=request.headers.get("api-key"))

    if request.method == "POST":
        form: TweetsPostForm = TweetsPostForm()
        data: dict = request.get_json()
        valid_data: dict = form.load(data)

        tweet_id: Any = Tweet.add(
            user=user,
            data=valid_data["tweet_data"],
            medias=valid_data["tweet_media_ids"]
        )

        if tweet_id:
            return jsonify({"result": True, "tweet_id": tweet_id}), 201
        else:
            raise ValueError("Не удалось создать твит.")

    elif request.method == "GET":
        result: list = list()

        for tweet in user.tweets:
            result.append({
                "id:": tweet.id,
                "content": tweet.tweet_data,
                "attachments": tweet.medias,
                "author": {"id": user.id, "name": user.name},
                "likes": [
                    {"user_id": u.id, "name": u.name} for u in tweet.tweet_likes
                ],
            })

        return jsonify({"result": True, "tweets": result}), 200

    else:
        raise MethodNotAllowed("Method not allowed")


@app.route("/api/medias", methods=["POST"])
@swag_from("./docs/medias.yml")
def medias():
    global file_count
    form: MediasPostForm = MediasPostForm()
    data: dict = {"file": request.files["file"]}
    valid_data: dict = form.load(data)

    file = valid_data["file"]
    filename: str = f"{file_count}-{secure_filename(file.filename)}"
    file.save(app.config['UPLOAD_FOLDER'] + filename)
    file_count += 1

    media_id: Any = Media.add(filename)

    if media_id:
        return jsonify({"result": True, "media_id": media_id}), 201
    else:
        raise ValueError("Не удалось сохранить изображение.")


@app.route("/api/tweets/<int:id_tweet>", methods=["DELETE"])
@swag_from("./docs/delete_tweet.yml")
def delete_tweet(id_tweet: int):
    user: Any = User.get_user(api_key=request.headers.get("api-key"))
    form: IdForm = IdForm()
    data: MultiDict = MultiDict([("act_id", id_tweet)])
    valid_data: MultiDict = form.load(data)

    tweet_id: int = valid_data["act_id"]

    if Tweet.delete(user, tweet_id):
        return jsonify({"result": True}), 200
    else:
        raise ValueError("Не удалось удалить твит или нет прав на действие.")


@app.route("/api/tweets/<int:id_tweet>/likes", methods=["POST", "DELETE"])
@swag_from("./docs/like_tweet_post.yml", methods=["POST"])
@swag_from("./docs/like_tweet_delete.yml", methods=["DELETE"])
def like_tweet(id_tweet: int):
    user: Any = User.get_user(api_key=request.headers.get("api-key"))
    form: IdForm = IdForm()
    data: MultiDict = MultiDict([("act_id", id_tweet)])
    valid_data: MultiDict = form.load(data)

    tweet_id: int = valid_data["act_id"]

    if request.method == "POST":
        if User.add_like(user, tweet_id):
            return jsonify({"result": True}), 200
        else:
            raise ValueError("Не удалось поставить лайк на твит.")

    elif request.method == "DELETE":
        if User.remove_like(user, tweet_id):
            return jsonify({"result": True}), 200
        else:
            raise ValueError("Не удалось удалить лайк с твита.")

    else:
        raise MethodNotAllowed("Method not allowed")


@app.route("/api/users/<int:id_user>/follow", methods=["POST", "DELETE"])
@swag_from("./docs/follow_post.yml", methods=["POST"])
@swag_from("./docs/follow_delete.yml", methods=["DELETE"])
def follow(id_user: int):
    user: Any = User.get_user(api_key=request.headers.get("api-key"))
    form: IdForm = IdForm()
    data: MultiDict = MultiDict([("act_id", id_user)])
    valid_data: MultiDict = form.load(data)

    user_id: int = valid_data["act_id"]

    if request.method == "POST":
        if User.add_following(user, user_id):
            return jsonify({"result": True}), 200
        else:
            raise ValueError("Не удалось подписаться на пользователя.")

    elif request.method == "DELETE":
        if User.remove_following(user, user_id):
            return jsonify({"result": True}), 200
        else:
            raise ValueError("Не удалось отписаться от пользователя.")

    else:
        raise MethodNotAllowed("Method not allowed")


@app.route("/api/users/me", methods=["GET"], endpoint="get_me")
@app.route("/api/users/<int:user_id>", methods=["GET"], endpoint="get_user")
@swag_from("./docs/me_me.yml", endpoint="get_me", methods=["GET"])
@swag_from("./docs/me_user_id.yml", endpoint="get_user", methods=["GET"])
def me(user_id: int = None):  # type: ignore
    user: Any = User.get_user(
        user_id=user_id,
        api_key=request.headers.get("api-key")
    )

    if user:
        return jsonify({
            "result": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "followers": [
                    {
                        "id": follower.id, "name": follower.name
                    } for follower in user.follower
                ],
                "following": [
                    {
                        "id": following.id, "name": following.name
                    } for following in user.following
                ]
            }
        }), 200
    else:
        raise ValueError("Пользователь не найден.")


@app.errorhandler(Exception)
def errorhandler(e: Exception):
    return jsonify({
        "result": False,
        "error_type": type(e).__name__,
        "error_message": str(e)
    }), 400
