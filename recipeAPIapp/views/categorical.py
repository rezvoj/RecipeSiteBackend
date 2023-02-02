import logging
from django.db import transaction
from django.db.models import Count, Q, Value
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404 as get
import recipeAPIapp.serializers.categorical as serializers
import recipeAPIapp.utils.filtering as filtering
import recipeAPIapp.utils.permission as permission
import recipeAPIapp.utils.validation as validation
from recipeAPIapp.models.user import User
from recipeAPIapp.models.categorical import Category, Ingredient, UserIngredient
from recipeAPIapp.models.recipe import Recipe
from recipeAPIapp.models.recipe import SubmitStatuses as Statuses

log = logging.getLogger(__name__)



class CategoryView(APIView):
    @transaction.atomic
    def post(self, request: Request):
        permission.admin_or_moderator(request)
        serializer = serializers.CategorySerializer(data=request.data)
        category: Category = validation.serializer(serializer).save()
        moderator_id = permission.user_id(request)
        log.info(f"Category created - category {category.pk}, moderator {moderator_id}")
        return Response({'id': category.pk}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def put(self, request: Request, category_id: int):
        permission.admin_or_moderator(request)
        category: Category = get(Category, pk=category_id)
        serializer = serializers.CategorySerializer(instance=category, data=request.data, partial=True)
        validation.serializer(serializer).save()
        moderator_id = permission.user_id(request)
        log.info(f"Category updated - category {category.pk}, moderator {moderator_id}")
        return Response({}, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request: Request, category_id: int):
        permission.admin_or_moderator(request)
        category: Category = get(Category, pk=category_id)
        if Recipe.objects.filter(categories=category, submit_status=Statuses.ACCEPTED).exists():
            permission.admin(request)
        category.delete()
        moderator_id = permission.user_id(request)
        log.info(f"Category deleted - category {category_id}, moderator {moderator_id}")
        return Response({}, status=status.HTTP_204_NO_CONTENT)
