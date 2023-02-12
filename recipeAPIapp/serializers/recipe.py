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


class RecipePhotoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipePhoto
        fields = ('photo', 'number')

    def __init__(self, *args, recipe: Recipe, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipe = recipe

    def validate_photo(self, value):
        return validation.photo(value)

    def validate(self, data):
        data = super().validate(data)
        self.photo_count = RecipePhoto.objects.filter(recipe=self.recipe).count()
        if Config.PerRecipeLimits.photos <= self.photo_count:
            raise serializers.ValidationError("photo limit exceeded.")
        return data

    def create(self, validated_data):
        validated_data['recipe'] = self.recipe
        validated_data['number'] = min(self.photo_count + 1, validated_data['number'])
        range = {'number__gte': validated_data['number']}
        for photo in RecipePhoto.objects.filter(recipe=self.recipe, **range):
            photo.number += 1
            photo.save()
        self.recipe.submit_status = Statuses.UNSUBMITTED
        self.recipe.deny_message = None
        self.recipe.save()
        return super().create(validated_data)


class RecipePhotoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipePhoto
        fields = ('photo', 'number')

    def validate_photo(self, value):
        return validation.photo(value)

    def update(self, instance: RecipePhoto, validated_data):
        if 'number' in validated_data and validated_data['number'] != instance.number:
            photo_count = RecipePhoto.objects.filter(recipe=instance.recipe).count()
            validated_data['number'] = min(photo_count, validated_data['number'])
            if validated_data['number'] > instance.number:
                range = {'number__gt': instance.number, 'number__lte': validated_data['number']}
                movement = -1
            else:
                range = {'number__gte': validated_data['number'], 'number__lt': instance.number}
                movement = 1
            for photo in RecipePhoto.objects.filter(recipe=instance.recipe, **range):
                photo.number += movement
                photo.save()
        instance.recipe.submit_status = Statuses.UNSUBMITTED
        instance.recipe.deny_message = None
        instance.recipe.save()
        return super().update(instance, validated_data)
