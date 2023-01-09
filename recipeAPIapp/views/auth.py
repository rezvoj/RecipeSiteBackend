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


class UpdateView(APIView):
    @transaction.atomic
    def put(self, request: Request):
        user: User = permission.user(request)
        user.refresh_from_db()
        serializer = serializers.UpdateSerializer(instance=user, data=request.data, partial=True)
        validation.serializer(serializer).save()
        token = security.generate_token(user)
        log.info(f"User auth updated - user {user.pk}")
        return Response({'token': token}, status=status.HTTP_200_OK)


class VerificationView(APIView):
    @transaction.atomic
    def post(self, request: Request):
        user: User = permission.user(request)
        user.refresh_from_db()
        limit = Config.ContentLimits.email_code
        dtm_offset = utc_now() - timedelta(hours=limit[1])
        EmailRecord.objects.filter(created_at__lte=dtm_offset).delete()
        if validation.is_limited(user, EmailRecord, limit):
            raise ContentLimitException({'limit': limit[0], 'hours': limit[1]})
        validation.serializer(serializers.SendVerificationSerializer(user=user, data={}))
        verification.Email.send(user)
        log.info(f"Verification email sent - user {user.pk}")
        return Response({}, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request: Request, code: str):
        user: User = permission.user(request)
        user.refresh_from_db()
        serializer = serializers.CompleteVerificationSerializer(user=user, code=code, data={})
        validation.serializer(serializer)
        user.vcode = user.vcode_expiry = None
        user.save()
        log.info(f"Email verified - user {user.pk}")
        return Response({}, status=status.HTTP_200_OK)
