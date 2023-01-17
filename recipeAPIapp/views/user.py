import logging
from django.db import transaction
from django.db.models import Q, Count, Avg
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404 as get
import recipeAPIapp.serializers.user as serializers
import recipeAPIapp.utils.permission as permission
import recipeAPIapp.utils.security as security
import recipeAPIapp.utils.validation as validation
from recipeAPIapp.apps import Config
from recipeAPIapp.utils.exception import ContentLimitException
from recipeAPIapp.models.user import User, UserReport
from recipeAPIapp.models.recipe import SubmitStatuses as Statuses

log = logging.getLogger(__name__)



class UserView(APIView):
    @transaction.atomic
    def post(self, request: Request):
        serializer = serializers.UserCreateSerializer(data=request.data)
        user: User = validation.serializer(serializer).save()
        token = security.generate_token(user)
        log.info(f"User created - user {user.pk}")
        return Response({'token': token}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def put(self, request: Request):
        user: User = permission.user(request)
        user.refresh_from_db()
        serializer = serializers.UserUpdateSerializer(instance=user, data=request.data, partial=True)
        validation.serializer(serializer).save()
        log.info(f"User updated - user {user.pk}")
        return Response({}, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request: Request):
        user: User = permission.user(request)
        user_id = user.pk
        user.delete()
        log.info(f"User deleted - user {user_id}")
        return Response({}, status=status.HTTP_204_NO_CONTENT)
