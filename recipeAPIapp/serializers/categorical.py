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


class CategorySmallData(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'photo', 'name')


class CategoryData(serializers.ModelSerializer):
    recipe_count = serializers.IntegerField()
    self_recipe_count = serializers.IntegerField()
    favoured = serializers.SerializerMethodField()

    def __init__(self, *args, user: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    class Meta:
        model = Category
        fields = CategorySmallData.Meta.fields + (
            'about', 'recipe_count', 'self_recipe_count', 'favoured'
        )

    def get_favoured(self, obj: Category):
        if isinstance(self.user, User):
            return obj.favoured_by.filter(pk=self.user.pk).exists()
        return None


class CategoryFilter(serializers.Serializer):
    favoured = serializers.BooleanField(default=False)
    search_string = serializers.CharField(required=False)
    order_by = serializers.ListField(child=serializers.CharField(), required=False)
    order_time_window = serializers.IntegerField(min_value=1, required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)

    def validate_order_by(self, value):
        return validation.order_by(value, ['name', 'recipe_count', 'self_recipe_count'])
