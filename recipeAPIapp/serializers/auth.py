from django.contrib.auth import password_validation
from rest_framework import serializers
import recipeAPIapp.utils.security as security
import recipeAPIapp.utils.verification as verification
from recipeAPIapp.models.user import User



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        data = super().validate(data)
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("invalid email or password.")
        if not security.check_password(user, data['password']):
            raise serializers.ValidationError("invalid email or password.")
        return data


class UpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=False)
    
    class Meta:
        model = User
        fields = ('password', 'email', 'new_password')

    def validate_password(self, value):
        if not security.check_password(self.instance, value):
            raise serializers.ValidationError("invalid password.")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value
    
    def validate(self, data):
        data = super().validate(data)
        if 'email' not in data and 'new_password' not in data:
            raise serializers.ValidationError("nothing to change.")
        return data

    def update(self, instance: User, validated_data: dict):
        validated_data.pop('password')
        instance.details_iteration += 1
        if 'new_password' in validated_data:
            password = validated_data.pop('new_password')
            security.set_password(instance, password)
        instance = super().update(instance, validated_data)
        if 'email' in validated_data:
            verification.Email.send(instance)
        return instance
