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


class CategoryFavourView(APIView):
    @transaction.atomic
    def post(self, request: Request, category_id: int):
        user: User = permission.verified(request)
        category: Category = get(Category, pk=category_id)
        favoured = category.favoured_by.filter(pk=user.pk).exists()
        if favoured:
            category.favoured_by.remove(user)
        else:
            category.favoured_by.add(user)
        return Response({}, status=status.HTTP_200_OK)


class CategoryFilterView(APIView):
    def get(self, request: Request):
        user = request.user
        serializer = serializers.CategoryFilter(data=request.query_params)
        vdata = validation.serializer(serializer).validated_data
        qryset = Category.objects.all()
        if vdata['favoured'] and isinstance(user, User):
            qryset = qryset.filter(favoured_by=user)
        if 'search_string' in vdata:
            qryset = filtering.search(qryset, ['name'], vdata['search_string'])
        qryset = qryset.annotate(recipe_count=Count('recipes', distinct=True), filter=Q(recipes__submit_status=Statuses.ACCEPTED))
        function = Count('recipes', distinct=True, filter=Q(recipes__user=user)) if isinstance(user, User) else Value(0)
        qryset = qryset.annotate(self_recipe_count=function)
        qryset = filtering.order_by(qryset, vdata, recipe_count=(Count, 'recipes', 'recipes'))
        result = filtering.paginate(qryset, vdata, lambda qs: serializers.CategoryData(qs, user=user, many=True).data)
        return Response(result, status=status.HTTP_200_OK)


class IngredientView(APIView):
    @transaction.atomic
    def post(self, request: Request):
        permission.admin_or_moderator(request)
        serializer = serializers.IngredientSerializer(data=request.data)
        ingredient: Ingredient = validation.serializer(serializer).save()
        moderator_id = permission.user_id(request)
        log.info(f"Ingredient created - ingredient {ingredient.pk}, moderator {moderator_id}")
        return Response({'id': ingredient.pk}, status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    def put(self, request: Request, ingredient_id: int):
        permission.admin_or_moderator(request)
        ingredient: Ingredient = get(Ingredient, pk=ingredient_id)
        serializer = serializers.IngredientSerializer(instance=ingredient, data=request.data, partial=True)
        validation.serializer(serializer).save()
        moderator_id = permission.user_id(request)
        log.info(f"Ingredient updated - ingredient {ingredient.pk}, moderator {moderator_id}")
        return Response({}, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request: Request, ingredient_id: int):
        permission.admin_or_moderator(request)
        ingredient: Ingredient = get(Ingredient, pk=ingredient_id)
        if Recipe.objects.filter(recipeingredient__ingredient=ingredient, submit_status=Statuses.ACCEPTED).exists():
            permission.admin(request)
        ingredient.delete()
        moderator_id = permission.user_id(request)
        log.info(f"Ingredient deleted - ingredient {ingredient_id}, moderator {moderator_id}")
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class IngredientInventoryView(APIView):
    @transaction.atomic
    def post(self, request: Request, ingredient_id: int):
        user: User = permission.verified(request)
        ingredient: Ingredient = get(Ingredient, pk=ingredient_id)
        serializer = serializers.AmountSerializer(data=request.data)
        vdata = validation.serializer(serializer).validated_data
        try:
            user_ingredient = UserIngredient.objects.get(user=user, ingredient=ingredient)
            user_ingredient.amount += vdata['amount']
            if user_ingredient.amount <= 0:
                user_ingredient.delete()
                response_status = status.HTTP_204_NO_CONTENT
            else:
                data = {'amount': user_ingredient.amount}
                serializer = serializers.AmountValueSerializer(data=data)
                validation.serializer(serializer)
                user_ingredient.save()
                response_status = status.HTTP_200_OK
        except UserIngredient.DoesNotExist:
            serializer = serializers.IngredientInventorySerializer(user=user, ingredient=ingredient, data=vdata)
            validation.serializer(serializer).save()
            response_status = status.HTTP_201_CREATED
        log.info(f"User inventory updated - user {user.pk}")
        return Response({}, status=response_status)

    @transaction.atomic
    def delete(self, request: Request, ingredient_id: int):
        user: User = permission.verified(request)
        user_ingredient: UserIngredient = get(UserIngredient, user=user, ingredient=ingredient_id)
        user_ingredient.delete()
        log.info(f"User inventory updated - user {user.pk}")
        return Response({}, status=status.HTTP_204_NO_CONTENT)
