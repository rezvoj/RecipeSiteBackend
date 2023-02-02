from decimal import Decimal
from rest_framework import serializers
import recipeAPIapp.utils.validation as validation
from recipeAPIapp.apps import Config
from recipeAPIapp.models.user import User
from recipeAPIapp.models.categorical import Category, Ingredient, UserIngredient



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('photo', 'name', 'about')

    def validate_photo(self, value):
        return validation.photo(value)
