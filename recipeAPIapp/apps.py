from django.apps import AppConfig


class Config(AppConfig):
    name = 'recipeAPIapp'

    class IssueFor:
        jwt_token = 7
        email_code = 3

    class PerRecipeLimits:
        categories = 10
        photos = 10
        instructions = 15
        ingredients = 20

    class ContentLimits:
        """ (pieces, per hours) """
        inventory_limit = 50
        email_code = (7, 1)
        recipe = (5, 24)
        recipe_moderator = (20, 24)
        rating = (15, 24)
        report = (15, 24)
