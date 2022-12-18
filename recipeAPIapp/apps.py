from django.apps import AppConfig


class Config(AppConfig):
    name = 'recipeAPIapp'

    class IssueFor:
        jwt_token = 7
        email_code = 3
