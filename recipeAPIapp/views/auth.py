import logging
from datetime import timedelta
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
import recipeAPIapp.serializers.auth as serializers
import recipeAPIapp.utils.permission as permission
import recipeAPIapp.utils.security as security
import recipeAPIapp.utils.validation as validation
import recipeAPIapp.utils.verification as verification
from recipeAPIapp.apps import Config
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.utils.exception import ContentLimitException
from recipeAPIapp.models.user import User, EmailRecord

log = logging.getLogger(__name__)



class TokenView(APIView):
    @transaction.atomic
    def post(self, request: Request):
        user: User = permission.user(request)
        user.refresh_from_db()
        token = security.generate_token(user)
        return Response({'token': token}, status=status.HTTP_200_OK)


class LoginView(APIView):
    @transaction.atomic
    def post(self, request: Request):
        serializer = serializers.LoginSerializer(data=request.data)
        serializer = validation.serializer(serializer)
        user = User.objects.get(email=serializer.validated_data['email'])
        token = security.generate_token(user)
        log.info(f"User logged in - user {user.pk}")
        return Response({'token': token}, status=status.HTTP_200_OK)
