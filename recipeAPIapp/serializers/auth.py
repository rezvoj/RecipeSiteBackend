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
