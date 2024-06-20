from flasgger import Schema, fields, ValidationError  # type: ignore
from marshmallow import validates, post_load


class TweetsPostForm(Schema):
    tweet_data = fields.Str(
        required=True,
        error_messages={
            "invalid": "Поле обязательно для заполнения в формате 'str'."
        }
    )
    tweet_media_ids = fields.List(fields.Int(
        required=True,
        error_messages={
            "invalid": "Список должен состоять из 'int' значений."
        }
    ))

    @post_load
    def returning_form(self, data: dict, **kwargs) -> dict:
        return data


class MediasPostForm(Schema):
    file = fields.Raw(
        metadata={'type': 'file'},
        required=True,
        error_messages={
            "invalid": "На вход требуется подать файл."
        }
    )

    @validates("file")
    def validate_file(self, file):
        allow_formats: list = ["jpg"]
        if file.filename.split(".")[-1] not in allow_formats:
            raise ValidationError("Данный формат файла не разрешен.")

    @post_load
    def returning_form(self, data: dict, **kwargs) -> dict:
        return data


class IdForm(Schema):
    act_id = fields.Int(
        required=True,
        error_messages={
            "invalid": "Значение должно быть положительным числом 'int' формата."
        }
    )

    @validates("act_id")
    def validate_act_id(self, act_id: int):
        if act_id < 1:
            raise ValidationError("Значение должно быть больше нуля.")

    @post_load
    def returning_form(self, data: dict, **kwargs) -> dict:
        return data
