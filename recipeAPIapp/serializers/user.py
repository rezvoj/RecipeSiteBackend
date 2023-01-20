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
