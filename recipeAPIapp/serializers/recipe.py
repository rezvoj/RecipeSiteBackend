from django.db.models import Avg, Min, ExpressionWrapper, IntegerField, DecimalField, Subquery, F, OuterRef, Value, Exists
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.request import Request
import recipeAPIapp.serializers.categorical as categorical_serializers
import recipeAPIapp.serializers.user as user_serializers
import recipeAPIapp.utils.permission as permission
import recipeAPIapp.utils.validation as validation
from recipeAPIapp.apps import Config
from recipeAPIapp.models.user import User
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.models.categorical import Category, Ingredient, UserIngredient
from recipeAPIapp.models.recipe import Recipe, RecipeInstruction, RecipePhoto, RecipeIngredient, Rating
from recipeAPIapp.models.recipe import SubmitStatuses as Statuses



class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('categories', 'name', 'title', 'prep_time', 'calories')

    def __init__(self, *args, user: User = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_categories(self, value):
        if len(value) > Config.PerRecipeLimits.categories:
            raise serializers.ValidationError("category limit exceeded.")
        return value

    def create(self, validated_data: dict):
        validated_data['user'] = self.user
        return super().create(validated_data)

    def update(self, instance: Recipe, validated_data):
        instance.submit_status = Statuses.UNSUBMITTED
        instance.deny_message = None
        return super().update(instance, validated_data)
