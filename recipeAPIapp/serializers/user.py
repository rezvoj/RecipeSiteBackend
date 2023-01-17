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
