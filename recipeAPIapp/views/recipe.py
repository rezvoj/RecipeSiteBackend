import logging
from decimal import Decimal
from django.db import transaction
from django.db.models import Count, Q, ExpressionWrapper, DecimalField, OuterRef, Exists, Avg, Value, F, Subquery
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404 as get
import recipeAPIapp.utils.permission as permission
import recipeAPIapp.serializers.recipe as serializers
import recipeAPIapp.serializers.categorical as categorical_serializers
import recipeAPIapp.utils.filtering as filtering
import recipeAPIapp.utils.validation as validation
from recipeAPIapp.apps import Config
from recipeAPIapp.utils.exception import ContentLimitException
from recipeAPIapp.models.user import User
from recipeAPIapp.models.categorical import Category, Ingredient, UserIngredient
from recipeAPIapp.models.recipe import Recipe, RecipePhoto, RecipeInstruction, RecipeIngredient, Rating
from recipeAPIapp.models.recipe import SubmitStatuses as Statuses

log = logging.getLogger(__name__)



class RecipeView(APIView):
    @transaction.atomic
    def post(self, request: Request):
        user: User = permission.verified(request)
        if not user.moderator and validation.is_limited(user, Recipe, Config.ContentLimits.recipe):
            limit = Config.ContentLimits.recipe
            raise ContentLimitException({'limit': limit[0], 'hours': limit[1]})
        elif user.moderator and validation.is_limited(user, Recipe, Config.ContentLimits.recipe_moderator):
            limit = Config.ContentLimits.recipe_moderator
            raise ContentLimitException({'limit': limit[0], 'hours': limit[1]})
        serializer = serializers.RecipeSerializer(user=user, data=request.data)
        recipe: Recipe = validation.serializer(serializer).save()
        log.info(f"Recipe created - recipe {recipe.pk}, user {user.pk}")
        return Response({'id': recipe.pk}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def put(self, request: Request, recipe_id: int):
        user: User = permission.verified(request)
        recipe: Recipe = get(Recipe, pk=recipe_id, user=user)
        serializer = serializers.RecipeSerializer(instance=recipe, data=request.data, partial=True)
        validation.serializer(serializer).save()
        log.info(f"Recipe updated - recipe {recipe.pk}, user {user.pk}")
        return Response({}, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request: Request, recipe_id: int):
        user: User = permission.verified(request)
        recipe: Recipe = get(Recipe, pk=recipe_id, user=user)
        recipe.delete()
        log.info(f"Recipe deleted - recipe {recipe_id}, user {user.pk}")
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class RecipePhotoView(APIView):
    @transaction.atomic
    def post(self, request: Request, id: int):
        user: User = permission.verified(request)
        recipe: Recipe = get(Recipe, pk=id, user=user)
        serializer = serializers.RecipePhotoCreateSerializer(recipe=recipe, data=request.data)
        validation.serializer(serializer).save()
        log.info(f"Recipe updated - recipe {recipe.pk}, user {user.pk}")
        return Response({}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def put(self, request: Request, id: int):
        user: User = permission.verified(request)
        photo: RecipePhoto = get(RecipePhoto, pk=id, recipe__user=user)
        serializer = serializers.RecipePhotoUpdateSerializer(instance=photo, data=request.data, partial=True)
        validation.serializer(serializer).save()
        log.info(f"Recipe updated - recipe {photo.recipe.pk}, user {user.pk}")
        return Response({}, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request: Request, id: int):
        user: User = permission.verified(request)
        photo: RecipePhoto = get(RecipePhoto, pk=id, recipe__user=user)
        for phto in RecipePhoto.objects.filter(recipe=photo.recipe, number__gt=photo.number):
            phto.number -= 1
            phto.save()
        photo.delete()
        photo.recipe.submit_status = Statuses.UNSUBMITTED
        photo.recipe.deny_message = None
        photo.recipe.save()
        log.info(f"Recipe updated - recipe {photo.recipe.pk}, user {user.pk}")
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class RecipeInstructionView(APIView):
    @transaction.atomic
    def post(self, request: Request, id: int):
        user: User = permission.verified(request)
        recipe: Recipe = get(Recipe, pk=id, user=user)
        serializer = serializers.RecipeInstructionCreateSerializer(recipe=recipe, data=request.data)
        validation.serializer(serializer).save()
        log.info(f"Recipe updated - recipe {recipe.pk}, user {user.pk}")
        return Response({}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def put(self, request: Request, id: int):
        user: User = permission.verified(request)
        instruction: RecipeInstruction = get(RecipeInstruction, pk=id, recipe__user=user)
        serializer = serializers.RecipeInstructionUpdateSerializer(instance=instruction, data=request.data, partial=True)
        validation.serializer(serializer).save()
        log.info(f"Recipe updated - recipe {instruction.recipe.pk}, user {user.pk}")
        return Response({}, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request: Request, id: int):
        user: User = permission.verified(request)
        instruction: RecipeInstruction = get(RecipeInstruction, pk=id, recipe__user=user)
        for instr in RecipeInstruction.objects.filter(recipe=instruction.recipe, number__gt=instruction.number):
            instr.number -= 1
            instr.save()
        instruction.delete()
        instruction.recipe.submit_status = Statuses.UNSUBMITTED
        instruction.recipe.deny_message = None
        instruction.recipe.save()
        log.info(f"Recipe updated - recipe {instruction.recipe.pk}, user {user.pk}")
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class RecipeIngredientView(APIView):
    @transaction.atomic
    def post(self, request: Request, recipe_id: int, ingredient_id: int):
        user: User = permission.verified(request)
        recipe: Recipe = get(Recipe, pk=recipe_id, user=user)
        ingredient: Ingredient = get(Ingredient, pk=ingredient_id)
        serializer = categorical_serializers.AmountSerializer(data=request.data)
        vdata = validation.serializer(serializer).validated_data
        try:
            recipe_ingredient = RecipeIngredient.objects.get(recipe=recipe, ingredient=ingredient)
            recipe_ingredient.amount += vdata['amount']
            if recipe_ingredient.amount <= 0:
                recipe_ingredient.delete()    
                response_status = status.HTTP_204_NO_CONTENT
            else:
                data = {'amount': recipe_ingredient.amount}
                serializer = categorical_serializers.AmountValueSerializer(data=data)
                validation.serializer(serializer)
                recipe_ingredient.save()
                response_status = status.HTTP_200_OK
        except RecipeIngredient.DoesNotExist:
            serializer = serializers.RecipeIngredientSerializer(recipe=recipe, ingredient=ingredient, data=vdata)
            validation.serializer(serializer).save()
            response_status = status.HTTP_201_CREATED
        recipe.submit_status = Statuses.UNSUBMITTED
        recipe.deny_message = None
        recipe.save()
        log.info(f"Recipe updated - recipe {recipe.pk}, user {user.pk}")
        return Response({}, status=response_status)

    @transaction.atomic
    def delete(self, request: Request, recipe_id: int, ingredient_id: int):
        user: User = permission.verified(request)
        recipe: Recipe = get(Recipe, pk=recipe_id, user=user)
        recipe_ingredient: RecipeIngredient = get(RecipeIngredient, recipe=recipe, ingredient=ingredient_id)
        recipe_ingredient.delete()
        recipe.submit_status = Statuses.UNSUBMITTED
        recipe.deny_message = None
        recipe.save()
        log.info(f"Recipe updated - recipe {recipe.pk}, user {user.pk}")
        return Response({}, status=status.HTTP_204_NO_CONTENT)
