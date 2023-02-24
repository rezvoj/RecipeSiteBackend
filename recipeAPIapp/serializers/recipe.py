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


class RecipeInstructionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeInstruction
        fields = ('photo', 'number', 'title', 'content')

    def __init__(self, *args, recipe: Recipe, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipe = recipe

    def validate_photo(self, value):
        return validation.photo(value)

    def validate(self, data):
        data = super().validate(data)
        self.instruction_count = RecipeInstruction.objects.filter(recipe=self.recipe).count()
        if Config.PerRecipeLimits.instructions <= self.instruction_count:
            raise serializers.ValidationError("instruction limit exceeded.")
        return data

    def create(self, validated_data):
        validated_data['recipe'] = self.recipe
        validated_data['number'] = min(self.instruction_count + 1, validated_data['number'])
        range = {'number__gte': validated_data['number']}
        for instruction in RecipeInstruction.objects.filter(recipe=self.recipe, **range):
            instruction.number += 1
            instruction.save()
        self.recipe.submit_status = Statuses.UNSUBMITTED
        self.recipe.deny_message = None
        self.recipe.save()
        return super().create(validated_data)


class RecipeInstructionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeInstruction
        fields = ('photo', 'number', 'title', 'content')

    def validate_photo(self, value):
        return validation.photo(value)

    def update(self, instance: RecipeInstruction, validated_data):
        if 'number' in validated_data and validated_data['number'] != instance.number:
            instruction_count = RecipeInstruction.objects.filter(recipe=instance.recipe).count()
            validated_data['number'] = min(instruction_count, validated_data['number'])
            if validated_data['number'] > instance.number:
                range = {'number__gt': instance.number, 'number__lte': validated_data['number']}
                movement = -1
            else:
                range = {'number__gte': validated_data['number'], 'number__lt': instance.number}
                movement = 1
            for instruction in RecipeInstruction.objects.filter(recipe=instance.recipe, **range):
                instruction.number += movement
                instruction.save()
        instance.recipe.submit_status = Statuses.UNSUBMITTED
        instance.recipe.deny_message = None
        instance.recipe.save()
        return super().update(instance, validated_data)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredient
        fields = ('amount',)

    def __init__(self, *args, recipe: Recipe, ingredient: Ingredient, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipe = recipe
        self.ingredient = ingredient

    def validate(self, data):
        data = super().validate(data)
        ingredient_count = RecipeIngredient.objects.filter(recipe=self.recipe).count()
        if Config.PerRecipeLimits.ingredients <= ingredient_count:
            raise serializers.ValidationError("ingredient limit exceeded.")
        return data
    
    def create(self, validated_data):
        validated_data['recipe'] = self.recipe
        validated_data['ingredient'] = self.ingredient
        return super().create(validated_data)


class RecipeSubmitSerializer(serializers.Serializer):
    def __init__(self, *args, recipe: Recipe, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipe = recipe

    def validate(self, data):
        if self.recipe.categories.count() == 0:
            raise serializers.ValidationError("categories can't be empty.")
        if RecipePhoto.objects.filter(recipe=self.recipe).count() == 0:
            raise serializers.ValidationError("photos can't be empty.")
        if RecipeInstruction.objects.filter(recipe=self.recipe).count() == 0:
            raise serializers.ValidationError("instructions can't be empty.")
        if RecipeIngredient.objects.filter(recipe=self.recipe).count() == 0:
            raise serializers.ValidationError("ingredients can't be empty.")
        return data


class RecipeDenySerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('deny_message',)

    def update(self, instance: Recipe, validated_data):
        instance.submit_status = Statuses.DENIED
        return super().update(instance, validated_data)


class RecipeCookSerializer(serializers.Serializer):
    servings = serializers.IntegerField(default=1, min_value=1)
    
    def __init__(self, *args, user: User, recipe: Recipe, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.recipe = recipe

    def validate(self, data):
        data = super().validate(data)
        servings_value = Value(data['servings'], output_field=DecimalField())
        expression = ExpressionWrapper(OuterRef('amount') * servings_value, output_field=DecimalField())
        subq = UserIngredient.objects.filter(user=self.user, ingredient=OuterRef('ingredient'), amount__gte=expression)
        if RecipeIngredient.objects.filter(recipe=self.recipe).filter(~Exists(subq)).count() > 0:
            raise serializers.ValidationError("insufficient ingredients.")
        return data


class RecipeSmallData(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    user = user_serializers.UserSmallData()

    class Meta:
        model = Recipe
        fields = (
            'id', 'photo', 'user', 'name', 'title', 
            'prep_time', 'calories', 'created_at',
        )

    def get_photo(self, obj: Recipe):
        recipe_photo = RecipePhoto.objects.filter(recipe=obj).order_by('number').first()
        return recipe_photo.photo.url if recipe_photo is not None else None


class RecipeBaseData(RecipeSmallData):
    rating_count = serializers.IntegerField()
    avg_rating = serializers.FloatField()
    favoured = serializers.SerializerMethodField()
    deny_message = serializers.SerializerMethodField()
    
    def __init__(self, *args, user: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    class Meta:
        model = Recipe
        fields = RecipeSmallData.Meta.fields + (
            'submit_status', 'deny_message',
            'rating_count', 'avg_rating', 'favoured',
        )

    def get_favoured(self, obj: Recipe):
        if isinstance(self.user, User):
            return obj.favoured_by.filter(pk=self.user.pk).exists()
        return None

    def get_deny_message(self, obj: Recipe):
        if obj.user == self.user:
            return obj.deny_message
        return None


class RecipePhotoData(serializers.ModelSerializer):
    class Meta:
        model = RecipePhoto
        fields = ('id', 'photo')


class RecipeInstructionData(serializers.ModelSerializer):
    class Meta:
        model = RecipeInstruction
        fields = ('id', 'photo', 'title', 'content')


class RecipeIngredientData(serializers.ModelSerializer):
    ingredient = categorical_serializers.IngredientSmallData()
    
    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')


class RecipeData(RecipeBaseData):
    rating_count = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    favoured_count = serializers.SerializerMethodField()
    cookable_portions = serializers.SerializerMethodField()
    categories = categorical_serializers.CategorySmallData(many=True)
    ingredients = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = RecipeBaseData.Meta.fields + (
            'cookable_portions', 'favoured_count',
            'categories', 'ingredients', 'photos', 'instructions'
        )

    def get_rating_count(self, obj: Recipe):
        return Rating.objects.filter(recipe=obj).count()

    def get_avg_rating(self, obj: Recipe):
        aggr = Rating.objects.filter(recipe=obj).aggregate(Avg('stars'))
        return aggr['stars__avg'] if aggr['stars__avg'] is not None else 0

    def get_favoured_count(self, obj: Recipe):
        return obj.favoured_by.count()
    
    def get_cookable_portions(self, obj: Recipe):
        if isinstance(self.user, User):
            subquery = Subquery(UserIngredient.objects.filter(user=self.user, ingredient=OuterRef('ingredient')).values('amount')[:1])
            expression = ExpressionWrapper(Coalesce(subquery, 0) / F('amount'), output_field=IntegerField())
            return RecipeIngredient.objects.filter(recipe=obj).annotate(TUH=expression).aggregate(min=Min('TUH'))['min']
        return None

    def get_ingredients(self, obj: Recipe):
        qryset = RecipeIngredient.objects.filter(recipe=obj)
        return [RecipeIngredientData(instance=ingredient).data for ingredient in qryset]

    def get_photos(self, obj: Recipe):
        qryset = RecipePhoto.objects.filter(recipe=obj).order_by('number')
        return [RecipePhotoData(instance=photo).data for photo in qryset]
    
    def get_instructions(self, obj: Recipe):
        qryset = RecipeInstruction.objects.filter(recipe=obj).order_by('number')
        return [RecipeInstructionData(instance=instruction).data for instruction in qryset]


class RecipeFilter(serializers.Serializer):
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, many=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(banned=False), required=False)
    submit_status = serializers.CharField(required=False)
    calories_limit = serializers.IntegerField(required=False, min_value=0)
    servings = serializers.IntegerField(default=1, min_value=1)
    prep_time_limit = serializers.IntegerField(required=False, min_value=0)
    favourite_category = serializers.BooleanField(default=False)
    sufficient_ingrediens = serializers.BooleanField(default=False)
    favoured = serializers.BooleanField(default=False)
    search_string = serializers.CharField(required=False)
    order_by = serializers.ListField(child=serializers.CharField(), required=False)
    order_time_window = serializers.IntegerField(min_value=1, required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)
    
    def __init__(self, *args, request: Request, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def validate_submit_status(self, value):
        user = User.objects.filter(pk=self.initial_data.get('user', None)).first()
        if isinstance(user, User) and user == self.request.user:
            valid_statuses = [Statuses.UNSUBMITTED, Statuses.SUBMITTED, Statuses.DENIED, Statuses.ACCEPTED]
        elif permission.is_admin_or_moderator(self.request):
            valid_statuses = [Statuses.SUBMITTED, Statuses.ACCEPTED]
        else:
            valid_statuses = [Statuses.ACCEPTED]
        if value not in valid_statuses:
            raise serializers.ValidationError("invalid submit_status value.")
        return value

    def validate_order_by(self, value):
        return validation.order_by(value, ['name', 'rating_count', 'avg_rating', 'prep_time', 'calories', 'created_at'])
