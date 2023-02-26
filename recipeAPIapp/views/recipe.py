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


class RecipeSubmitView(APIView):
    @transaction.atomic
    def put(self, request: Request, recipe_id: int):
        user: User = permission.verified(request)
        recipe: Recipe = get(Recipe, pk=recipe_id, user=user, submit_status=Statuses.UNSUBMITTED)
        serializer = serializers.RecipeSubmitSerializer(recipe=recipe, data={})
        validation.serializer(serializer)
        recipe.submit_status = Statuses.ACCEPTED if user.moderator else Statuses.SUBMITTED
        recipe.save()
        log.info(f"Recipe submitted - recipe {recipe.pk}, user {user.pk}")
        return Response({}, status=status.HTTP_200_OK)


class RecipeAcceptView(APIView):
    @transaction.atomic
    def put(self, request: Request, recipe_id: int):
        permission.admin_or_moderator(request)
        recipe: Recipe = get(Recipe, pk=recipe_id, submit_status=Statuses.SUBMITTED)
        recipe.submit_status = Statuses.ACCEPTED
        recipe.save()
        log.info(f"Recipe accepted - recipe {recipe.pk}, moderator {permission.user_id(request)}")
        return Response({}, status=status.HTTP_200_OK)


class RecipeDenyView(APIView):
    @transaction.atomic
    def put(self, request: Request, recipe_id: int):
        permission.admin_or_moderator(request)
        recipe: Recipe = get(Recipe, pk=recipe_id, submit_status=Statuses.SUBMITTED)
        serializer = serializers.RecipeDenySerializer(instance=recipe, data=request.data)
        validation.serializer(serializer).save()
        log.info(f"Recipe denied - recipe {recipe.pk}, moderator {permission.user_id(request)}")
        return Response({}, status=status.HTTP_200_OK)


class RecipeCookView(APIView):
    @transaction.atomic
    def post(self, request: Request, recipe_id: int):
        user: User = permission.verified(request)
        recipe: Recipe = get(Recipe, pk=recipe_id, submit_status=Statuses.ACCEPTED)
        serializer = serializers.RecipeCookSerializer(user=user, recipe=recipe, data=request.data)
        servings_value = Value(validation.serializer(serializer).validated_data['servings'], output_field=DecimalField())
        subquery = RecipeIngredient.objects.filter(recipe=recipe, ingredient=OuterRef('ingredient'))
        subquery = Subquery(subquery.values('amount'), output_field=DecimalField())
        query = UserIngredient.objects.filter(user=user, ingredient__recipeingredient__recipe=recipe)
        query.update(amount = F('amount') - subquery * servings_value)
        UserIngredient.objects.filter(user=user, amount=Decimal(0)).delete()
        log.info(f"User inventory updated - user {user.pk}")
        return Response({}, status=status.HTTP_200_OK)


class RecipeFavourView(APIView):
    @transaction.atomic
    def post(self, request: Request, recipe_id: int):
        user: User = permission.verified(request)
        recipe: Recipe = get(Recipe, pk=recipe_id, submit_status=Statuses.ACCEPTED)
        favoured = recipe.favoured_by.filter(pk=user.pk).exists()
        if favoured:
            recipe.favoured_by.remove(user)
        else:
            recipe.favoured_by.add(user)
        return Response({}, status=status.HTTP_200_OK)


class RecipeDetailView(APIView):
    def get(self, request: Request, recipe_id):
        user = request.user
        recipe: Recipe = get(Recipe, pk=recipe_id)
        if recipe.user == user:
            valid_statuses = [Statuses.UNSUBMITTED, Statuses.SUBMITTED, Statuses.DENIED, Statuses.ACCEPTED]
        elif permission.is_admin_or_moderator(request):
            valid_statuses = [Statuses.SUBMITTED, Statuses.ACCEPTED]
        else:
            valid_statuses = [Statuses.ACCEPTED]
        if recipe.submit_status not in valid_statuses:
            raise Http404()
        serializer = serializers.RecipeData(instance=recipe, user=user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeFilterView(APIView):
    def get(self, request: Request):
        user = request.user
        serializer = serializers.RecipeFilter(request=request, data=request.query_params)
        vdata = validation.serializer(serializer).validated_data
        if 'submit_status' in vdata:
            qryset = Recipe.objects.filter(submit_status=vdata['submit_status'])
        else:
            qryset = Recipe.objects.filter(submit_status=Statuses.ACCEPTED)
        if isinstance(user, User):
            if vdata['favourite_category']:
                qryset = qryset.filter(categories__in=Category.objects.filter(favoured_by=user)).distinct()
            if vdata['favoured']:
                qryset = qryset.filter(favoured_by=user)
            if vdata['sufficient_ingrediens']:
                servings_value = Value(vdata['servings'], output_field=DecimalField())
                expression = ExpressionWrapper(OuterRef('amount') * servings_value, output_field=DecimalField())
                subq = UserIngredient.objects.filter(user=user, ingredient=OuterRef('ingredient'), amount__gte=expression)
                qryset = qryset.filter(~Exists(RecipeIngredient.objects.filter(recipe_id=OuterRef('pk')).filter(~Exists(subq))))
        if 'categories' in vdata and len(vdata['categories']):
            qryset = qryset.filter(categories__in=vdata['categories']).distinct()
        if 'user' in vdata:
            qryset = qryset.filter(user=vdata['user'])
        if 'calories_limit' in vdata:
            qryset = qryset.filter(calories__lte=(vdata['calories_limit'] / vdata['servings']))
        if 'prep_time_limit' in vdata:
            qryset = qryset.filter(prep_time__lte=vdata['prep_time_limit'])
        if 'search_string' in vdata:
            qryset = filtering.search(qryset, ['name', 'title'], vdata['search_string'])
        qryset = qryset.annotate(rating_count=Count('rating', distinct=True))
        qryset = qryset.annotate(avg_rating=Avg('rating__stars', distinct=True))
        replace = {
            'rating_count': (Count, 'rating', 'rating'), 
            'avg_rating': (Avg, 'rating__stars', 'rating')
        }
        qryset = filtering.order_by(qryset, vdata, **replace)
        result = filtering.paginate(qryset, vdata, lambda qs: serializers.RecipeBaseData(qs, user=user, many=True).data)
        return Response(result, status=status.HTTP_200_OK)


class RatingView(APIView):
    @transaction.atomic
    def post(self, request: Request, id: int):
        user: User = permission.verified(request)
        if validation.is_limited(user, Rating, Config.ContentLimits.rating):
            limit = Config.ContentLimits.rating
            raise ContentLimitException({'limit': limit[0], 'hours': limit[1]})
        request.data['recipe'] = id
        serializer = serializers.RatingCreateSerializer(user=user, data=request.data)
        rating: Rating = validation.serializer(serializer).save()
        log.info(f"Rating created - rating {rating.pk}, user {user.pk}")
        return Response({'id': rating.pk}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def put(self, request: Request, id: int):
        user: User = permission.verified(request)
        rating: Rating = get(Rating, pk=id, user=user)
        serializer = serializers.RatingUpdateSerializer(instance=rating, data=request.data, partial=True)
        validation.serializer(serializer).save()
        log.info(f"Rating updated - rating {rating.pk}, user {user.pk}")
        return Response({}, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request: Request, id: int):
        user: User = permission.verified(request)
        rating: Rating = get(Rating, pk=id, user=user)
        rating.delete()
        log.info(f"Rating deleted - rating {id}, user {user.pk}")
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class RatingLikeView(APIView):
    @transaction.atomic
    def post(self, request: Request, rating_id: int):
        user: User = permission.user(request)
        rating: Rating = get(Rating, pk=rating_id, recipe__submit_status=Statuses.ACCEPTED)
        liked = rating.liked_by.filter(pk=user.pk).exists()
        if liked:
            rating.liked_by.remove(user)
        else:
            rating.liked_by.add(user)
        return Response({}, status=status.HTTP_200_OK)


class RatingFilterView(APIView):
    def get(self, request: Request):
        user = request.user
        serializer = serializers.RatingFilter(data=request.query_params)
        vdata = validation.serializer(serializer).validated_data
        qryset = Rating.objects.filter(recipe__submit_status=Statuses.ACCEPTED)
        if 'recipe' in vdata:
            serializer = serializers.RatingRecipeData
            qryset = qryset.filter(recipe=vdata['recipe'])
        elif 'user' in vdata:
            serializer = serializers.RatingUserData
            qryset = qryset.filter(user=vdata['user'])
        else:
            serializer = serializers.RatingData
        if isinstance(user, User) and vdata['liked']:
            qryset = qryset.filter(liked_by=user)
        if vdata['has_content']:
            qryset = qryset.filter(Q(content__isnull=False) | (Q(photo__isnull=False) & ~Q(photo='')))
        if 'search_string' in vdata:
            qryset = filtering.search(qryset, ['content'], vdata['search_string'])
        qryset = qryset.annotate(like_count=Count('liked_by', distinct=True))
        qryset = filtering.order_by(qryset, vdata)
        result = filtering.paginate(qryset, vdata, lambda qs: serializer(qs, user=user, many=True).data)
        return Response(result, status=status.HTTP_200_OK)
