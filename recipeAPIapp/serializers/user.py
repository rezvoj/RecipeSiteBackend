from django.db.models import Avg
from django.contrib.auth import password_validation
from rest_framework import serializers
import recipeAPIapp.utils.security as security
import recipeAPIapp.utils.validation as validation
import recipeAPIapp.utils.verification as verification
from recipeAPIapp.models.user import User, UserReport
from recipeAPIapp.models.recipe import Recipe, Rating
from recipeAPIapp.models.recipe import SubmitStatuses as Statuses



class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('photo', 'email', 'name', 'about', 'password')

    def validate_photo(self, value):
        return validation.photo(value)
    
    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data: dict):
        password = validated_data.pop('password')
        user: User = super().create(validated_data)
        security.set_password(user, password)
        user.save()
        verification.Email.send(user)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('photo', 'name', 'about')

    def validate_photo(self, value):
        return validation.photo(value)


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReport
        fields = ()

    def __init__(self, *args, user: User, reported: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.reported = reported
    
    def validate(self, data):
        data = super().validate(data)
        if UserReport.objects.filter(user=self.user, reported=self.reported).exists():
            raise serializers.ValidationError("user already reported.")
        return data

    def create(self, validated_data):
        validated_data['user'] = self.user
        validated_data['reported'] = self.reported
        return super().create(validated_data)


class UserSmallData(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'photo', 'name', 'created_at')


class UserFilterData(serializers.ModelSerializer):
    rating_count = serializers.IntegerField()
    recipe_count = serializers.IntegerField()
    avg_rating = serializers.FloatField()

    class Meta:
        model = User
        fields = UserSmallData.Meta.fields + ('rating_count', 'recipe_count', 'avg_rating')


class UserModeratorFilterData(UserFilterData):
    report_count = serializers.IntegerField()

    class Meta:
        model = User
        fields = UserFilterData.Meta.fields + ('moderator', 'report_count')


class UserData(serializers.ModelSerializer):
    rating_count = serializers.SerializerMethodField()
    recipe_count = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserFilterData.Meta.fields + ('about',)
    
    def get_rating_count(self, obj: User):
        return Rating.objects.filter(recipe__user=obj).count()

    def get_recipe_count(self, obj: User):
        return Recipe.objects.filter(user=obj, submit_status=Statuses.ACCEPTED).count()
    
    def get_avg_rating(self, obj: User):
        return Rating.objects.filter(recipe__user=obj).aggregate(Avg('stars'))['stars__avg'] or 0 


class UserModeratorData(UserData):
    report_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserData.Meta.fields + ('email', 'moderator', 'report_count',)

    def get_report_count(self, obj: User):
        return UserReport.objects.filter(reported=obj).count()


class UserSelfData(UserData):
    verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserData.Meta.fields + ('email', 'moderator', 'verified')

    def get_verified(self, obj: User):
        return obj.vcode is None


class UserFilter(serializers.Serializer):
    moderator = serializers.BooleanField(default=False)
    search_string = serializers.CharField(required=False)
    order_by = serializers.ListField(child=serializers.CharField(), required=False)
    order_time_window = serializers.IntegerField(min_value=1, required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)

    def __init__(self, *args, mod: bool, **kwargs):
        super().__init__(*args, **kwargs)
        self.mod = mod

    def validate_order_by(self, value):
        params = ['report_count'] if self.mod else []
        return validation.order_by(value, ['name', 'recipe_count', 'avg_rating'] + params)
