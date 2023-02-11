from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch
from django.test import override_settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
import recipeAPIapp.utils.security as security
import recipeAPIapp.tests.media_utils as media_utils
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.models.user import User
from recipeAPIapp.models.recipe import Recipe, Rating, RecipeInstruction, RecipeIngredient, RecipePhoto, SubmitStatuses
from recipeAPIapp.models.categorical import Category, Ingredient, UserIngredient



@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
class TestRecipeCUD(APITestCase):    
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.moderator = User.objects.create(email="moderator@example.com", name="Moderator", moderator=True)
        self.moderator_token = security.generate_token(self.moderator)
        self.category1 = Category.objects.create(name="Category 1", photo=media_utils.generate_test_image())
        self.category2 = Category.objects.create(name="Category 2", photo=media_utils.generate_test_image())

    def tearDown(self):
        media_utils.delete_test_media()

    def test_create_recipe(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            '/recipe', data={
                'name': 'New Recipe', 'title': 'New Recipe Title',
                'categories': [self.category1.pk], 'prep_time': 30, 'calories': 200
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        new_recipe = Recipe.objects.get(pk=response.data['id'])
        self.assertEqual(new_recipe.name, 'New Recipe')
        self.assertEqual(new_recipe.title, 'New Recipe Title')
        self.assertEqual(new_recipe.prep_time, 30)
        self.assertEqual(new_recipe.calories, 200)
        self.assertEqual(new_recipe.user, self.user)
        self.assertIn(self.category1, new_recipe.categories.all())

    @patch('recipeAPIapp.apps.Config.PerRecipeLimits.categories', 1)
    def test_create_recipe_category_limit_exceeded(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        categories = [self.category1.pk, self.category2.pk]
        response: Response = self.client.post(
            '/recipe', data={
                'name': 'Some Recipe', 'title': 'Recipe with too many categories',
                'categories': categories, 'prep_time': 30, 'calories': 200
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'categories': ['category limit exceeded.']}})

    @patch('recipeAPIapp.apps.Config.ContentLimits.recipe', (1, 24))
    def test_create_recipe_limit_exceeded_for_regular_user(self):
        Recipe.objects.create(
            user=self.user, name="Existing Recipe", 
            title="Existing Recipe Title", prep_time=30, calories=200
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            '/recipe', data={
                'name': 'New Recipe', 'title': 'New Recipe Title',
                'categories': [self.category1.pk], 'prep_time': 30, 'calories': 200
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'limit': 1, 'hours': 24}})

    @patch('recipeAPIapp.apps.Config.ContentLimits.recipe_moderator', (1, 24))
    def test_create_recipe_limit_exceeded_for_moderator(self):
        Recipe.objects.create(
            user=self.moderator, name="Existing Recipe", 
            title="Existing Recipe Title", prep_time=30, calories=200
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.post(
            '/recipe', data={
                'name': 'New Recipe', 'title': 'New Recipe Title',
                'categories': [self.category1.pk], 'prep_time': 30, 'calories': 200
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'limit': 1, 'hours': 24}})

    def test_update_recipe(self):
        recipe = Recipe.objects.create(
            user=self.user, name="Original Recipe", 
            title="Original Recipe Title", prep_time=30, calories=200
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(
            f'/recipe/{recipe.pk}', data={
                'name': 'Updated Recipe', 'title': 'Updated Recipe Title',
                'prep_time': 45, 'calories': 300
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.name, 'Updated Recipe')
        self.assertEqual(recipe.title, 'Updated Recipe Title')
        self.assertEqual(recipe.prep_time, 45)
        self.assertEqual(recipe.calories, 300)

    def test_update_recipe_unauthorized(self):
        recipe = Recipe.objects.create(
            user=self.user, name="Original Recipe", 
            title="Original Recipe Title", prep_time=30, calories=200
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(
            f'/recipe/{recipe.pk}', data={
                'name': 'Unauthorized Update',
                'title': 'This should fail',
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        recipe.refresh_from_db()
        self.assertNotEqual(recipe.name, 'Unauthorized Update')
        self.assertNotEqual(recipe.title, 'This should fail')

    def test_delete_recipe(self):
        recipe = Recipe.objects.create(
            user=self.user, name="Recipe to delete", 
            title="Recipe to delete Title", prep_time=30, calories=200
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.delete(f'/recipe/{recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(pk=recipe.pk).exists())

    def test_delete_recipe_unauthorized(self):
        recipe = Recipe.objects.create(
            user=self.user, name="Recipe to delete", 
            title="Recipe to delete Title", prep_time=30, calories=200
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/recipe/{recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(pk=recipe.pk).exists())

    def test_create_recipe_unauthorized(self):
        self.user.vcode = "NotNone"
        self.user.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            '/recipe', data={
                'name': 'New Recipe', 'title': 'New Recipe Title',
                'categories': [self.category1.pk], 'prep_time': 30, 'calories': 200,
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Recipe.objects.filter(name='New Recipe').exists())
