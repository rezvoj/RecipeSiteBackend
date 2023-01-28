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
import recipeAPIapp.utils.filtering as filtering
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


class ChangeModeratorView(APIView):
    @transaction.atomic
    def put(self, request: Request, user_id: int):
        permission.admin(request)
        user: User = get(User, pk=user_id, banned=False)
        user.moderator = not user.moderator
        user.save()
        action = "named" if user.moderator else "revoked"
        log.info(f"User {action} moderator - user {user.pk}")
        return Response({}, status=status.HTTP_200_OK)


class ReportView(APIView):
    @transaction.atomic
    def post(self, request: Request, user_id: int):
        user: User = permission.user(request)
        if validation.is_limited(user, UserReport, Config.ContentLimits.report):
            limit = Config.ContentLimits.report
            raise ContentLimitException({'limit': limit[0], 'hours': limit[1]})
        reported: User = get(User, pk=user_id, banned=False)
        serializer = serializers.ReportSerializer(user=user, reported=reported, data={})
        validation.serializer(serializer).save()
        return Response({}, status=status.HTTP_201_CREATED)


class UserBanView(APIView):
    @transaction.atomic
    def post(self, request: Request, user_id: int):
        permission.admin_or_moderator(request)
        filter_data = {'pk': user_id, 'banned': False} 
        if not permission.is_admin(request):
            filter_data |= {'moderator': False}
        reported: User = get(User, **filter_data)
        reported_id = reported.pk
        reported.delete()
        reported.banned = True
        reported.moderator = False
        reported.pk = reported.photo = None
        reported.save()
        moderator_id = permission.user_id(request)
        log.info(f"User banned - moderator {moderator_id}, banned {reported_id}")
        return Response({}, status=status.HTTP_200_OK)


class DismissReportsView(APIView):
    @transaction.atomic
    def delete(self, request: Request, user_id: int):
        permission.admin_or_moderator(request)        
        filter_data = {'pk': user_id, 'banned': False} 
        if not permission.is_admin(request):
            filter_data |= {'moderator': False}
        reported: User = get(User, **filter_data)
        UserReport.objects.filter(reported=reported).delete()
        moderator_id = permission.user_id(request)
        log.info(f"User reports dismissed - moderator {moderator_id}, reported {reported.pk}")
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class UserDetailView(APIView):
    def get(self, request: Request, user_id: int):
        moderator = permission.is_admin_or_moderator(request)
        user: User = get(User, pk=user_id, banned=False)
        serializer = serializers.UserModeratorData if moderator else serializers.UserData
        return Response(serializer(instance=user).data, status=status.HTTP_200_OK)


class UserSelfDetailView(APIView):
    def get(self, request: Request):
        user: User = permission.user(request)
        serializer = serializers.UserSelfData(instance=user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserFilterView(APIView):
    def get(self, request: Request):
        admin = permission.is_admin(request)
        moderator = admin or (isinstance(request.user, User) and request.user.moderator)
        serializer = serializers.UserFilter(data=request.query_params, mod=moderator)
        vdata = validation.serializer(serializer).validated_data
        qryset = User.objects.filter(banned=False)
        if vdata['moderator'] and admin:
            qryset = qryset.filter(moderator=True)
        if 'search_string' in vdata:
            qryset = filtering.search(qryset, ['name'], vdata['search_string'])
        filter = Q(recipe__submit_status=Statuses.ACCEPTED)
        qryset = qryset.annotate(recipe_count=Count('recipe', distinct=True), filter=filter)
        qryset = qryset.annotate(rating_count=Count('recipe__rating', distinct=True))
        qryset = qryset.annotate(avg_rating=Avg('recipe__rating__stars', distinct=True))
        if moderator:
            qryset = qryset.annotate(report_count=Count('reported', distinct=True))
        replace = {
            'recipe_count': (Count, 'recipe', 'recipe'),
            'rating_count': (Count, 'recipe__rating', 'recipe__rating'),
            'avg_rating': (Avg, 'recipe__rating__stars', 'recipe__rating'),           
            **({'report_count': (Count, 'reported', 'reported')} if moderator else {})
        }
        qryset = filtering.order_by(qryset, vdata, **replace)
        serializer = serializers.UserModeratorFilterData if moderator else serializers.UserFilterData
        result = filtering.paginate(qryset, vdata, lambda qs: serializer(qs, many=True).data)
        return Response(result, status=status.HTTP_200_OK)
