from decimal import Decimal
from unittest.mock import patch
from django.test import override_settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
import recipeAPIapp.utils.security as security
import recipeAPIapp.tests.media_utils as media_utils
from recipeAPIapp.models.user import User
from recipeAPIapp.models.categorical import Category, Ingredient, UserIngredient
from recipeAPIapp.models.recipe import Recipe, RecipeIngredient, SubmitStatuses



@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestCategoryCUD(APITestCase):    
    def setUp(self):
        self.moderator_user = User.objects.create(email="moderator@example.com", name="Moderator", moderator=True)
        self.moderator_token = security.generate_token(self.moderator_user)
        self.regular_user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.regular_user)

    def tearDown(self):
        media_utils.delete_test_media()

    def test_create_category_as_moderator(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.post(
            '/category', data={
                "name": "New Category", "about": "This is a new category.",
                "photo": media_utils.generate_test_image()
            }, format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        new_category = Category.objects.get(pk=response.data['id'])
        self.assertEqual(new_category.name, "New Category")
        self.assertEqual(new_category.about, "This is a new category.")
        self.assertTrue(new_category.photo)

    def test_update_category_as_moderator(self):
        category = Category.objects.create(
            name="Original Category", about="Original about",
            photo=media_utils.generate_test_image()
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(
            f'/category/{category.pk}', data={
                "name": "Updated Category", "about": "This is the updated category."
            }, format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category.refresh_from_db()
        self.assertEqual(category.name, "Updated Category")
        self.assertEqual(category.about, "This is the updated category.")
        self.assertTrue(category.photo)

    def test_delete_category_as_moderator(self):
        category = Category.objects.create(
            name="Category to delete", about="To be deleted",
            photo=media_utils.generate_test_image()
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/category/{category.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_delete_category_with_accepted_recipes_as_moderator(self):
        category = Category.objects.create(
            name="Category with Recipe", about="Cannot delete", 
            photo=media_utils.generate_test_image()
        )
        recipe = Recipe.objects.create(user=self.regular_user, name="Recipe", title="Title", prep_time=10, calories=100)
        recipe.categories.add(category)
        recipe.submit_status = SubmitStatuses.ACCEPTED
        recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/category/{category.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())

    def test_create_category_unauthorized(self):
        data = {"name": "Unauthorized Category", "photo": media_utils.generate_test_image()}
        response: Response = self.client.post('/category', data=data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Category.objects.filter(name="Unauthorized Category").exists())
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post('/category', data=data, format='multipart', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_category_unauthorized(self):
        category = Category.objects.create(
            name="Original Category", about="Original about",
            photo=media_utils.generate_test_image()
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(
            f'/category/{category.pk}', data={
                "name": "Unauthorized Update",
                "about": "This should fail."
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        category.refresh_from_db()
        self.assertNotEqual(category.name, "Unauthorized Update")
        self.assertNotEqual(category.about, "This should fail.")

    def test_delete_category_unauthorized(self):
        category = Category.objects.create(
            name="Category to delete", about="To be deleted",
            photo=media_utils.generate_test_image()
        )
        response: Response = self.client.delete(f'/category/{category.pk}', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.delete(f'/category/{category.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())

    def test_delete_category_with_no_accepted_recipes_as_moderator(self):
        category = Category.objects.create(
            name="Category with Recipe", about="Can delete",
            photo=media_utils.generate_test_image()
        )
        recipe = Recipe.objects.create(user=self.regular_user, name="Recipe", title="Title", prep_time=10, calories=100)
        recipe.categories.add(category)
        recipe.submit_status = SubmitStatuses.SUBMITTED
        recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/category/{category.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())
        self.assertTrue(Recipe.objects.filter(pk=recipe.pk).exists())


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
class TestCategoryFavour(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.category = Category.objects.create(name="Category", photo=media_utils.generate_test_image())
    
    def tearDown(self):
        media_utils.delete_test_media()
    
    def test_add_category_to_favourites(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/category/change-favourite/{self.category.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.category.favoured_by.filter(pk=self.user.pk).exists())
    
    def test_remove_category_from_favourites(self):
        self.category.favoured_by.add(self.user)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/category/change-favourite/{self.category.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.category.favoured_by.filter(pk=self.user.pk).exists())
    
    def test_favour_non_existent_category(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post('/category/change-favourite/999', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_favour_category_unauthorized(self):
        response: Response = self.client.post(f'/category/change-favourite/{self.category.pk}', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        unverified_user = User.objects.create(email="unverified@example.com", name="Unverified User", vcode="NotNone")
        unverified_token = security.generate_token(unverified_user)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {unverified_token}'}
        response: Response = self.client.post(f'/category/change-favourite/{self.category.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
