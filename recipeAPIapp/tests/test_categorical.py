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


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestIngredientCUD(APITestCase):    
    def setUp(self):
        self.moderator_user = User.objects.create(email="moderator@example.com", name="Moderator", moderator=True)
        self.moderator_token = security.generate_token(self.moderator_user)
        self.regular_user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.regular_user)

    def tearDown(self):
        media_utils.delete_test_media()

    def test_create_ingredient_as_moderator(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.post(
            '/ingredient', data={
                "name": "New Ingredient", "about": "This is a new ingredient.", "unit": "kg",
                "photo": media_utils.generate_test_image()
            }, format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        new_ingredient = Ingredient.objects.get(pk=response.data['id'])
        self.assertEqual(new_ingredient.name, "New Ingredient")
        self.assertEqual(new_ingredient.about, "This is a new ingredient.")
        self.assertEqual(new_ingredient.unit, "kg")
        self.assertTrue(new_ingredient.photo)

    def test_update_ingredient_as_moderator(self):
        ingredient = Ingredient.objects.create(
            name="Original Ingredient", about="Original about", unit="kg",
            photo=media_utils.generate_test_image()
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(
            f'/ingredient/{ingredient.pk}', data={
                "name": "Updated Ingredient", "about": "This is the updated ingredient."
            }, format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, "Updated Ingredient")
        self.assertEqual(ingredient.about, "This is the updated ingredient.")
        self.assertTrue(ingredient.photo)

    def test_delete_ingredient_as_moderator(self):
        ingredient = Ingredient.objects.create(
            name="Ingredient to delete", about="To be deleted", unit="kg",
            photo=media_utils.generate_test_image()
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/ingredient/{ingredient.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(pk=ingredient.pk).exists())

    def test_delete_ingredient_with_accepted_recipes_as_moderator(self):
        ingredient = Ingredient.objects.create(
            name="Ingredient with Recipe", about="Cannot delete", unit="kg", 
            photo=media_utils.generate_test_image()
        )
        recipe = Recipe.objects.create(user=self.regular_user, name="Recipe", title="Title", prep_time=10, calories=100)
        RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, amount=1.0)
        recipe.submit_status = SubmitStatuses.ACCEPTED
        recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/ingredient/{ingredient.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Ingredient.objects.filter(pk=ingredient.pk).exists())

    def test_create_ingredient_unauthorized(self):
        data = {
            "name": "Unauthorized Ingredient", "unit": "kg",
            "photo": media_utils.generate_test_image()
        }
        response: Response = self.client.post('/ingredient', data=data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Ingredient.objects.filter(name="Unauthorized Ingredient").exists())
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post('/ingredient', data=data, format='multipart', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_ingredient_unauthorized(self):
        ingredient = Ingredient.objects.create(
            name="Original Ingredient", about="Original about", unit="kg",
            photo=media_utils.generate_test_image()
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(
            f'/ingredient/{ingredient.pk}', data={
                "name": "Unauthorized Update", "about": "This should fail."
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        ingredient.refresh_from_db()
        self.assertNotEqual(ingredient.name, "Unauthorized Update")
        self.assertNotEqual(ingredient.about, "This should fail.")

    def test_delete_ingredient_unauthorized(self):
        ingredient = Ingredient.objects.create(
            name="Ingredient to delete", about="To be deleted", unit="kg",
            photo=media_utils.generate_test_image()
        )
        response: Response = self.client.delete(f'/ingredient/{ingredient.pk}', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.delete(f'/ingredient/{ingredient.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Ingredient.objects.filter(pk=ingredient.pk).exists())

    def test_delete_ingredient_with_no_accepted_recipes_as_moderator(self):
        ingredient = Ingredient.objects.create(
            name="Ingredient with Recipe", about="Can delete", unit="kg",
            photo=media_utils.generate_test_image()
        )
        recipe = Recipe.objects.create(user=self.regular_user, name="Recipe", title="Title", prep_time=10, calories=100)
        RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, amount=1.0)
        recipe.submit_status = SubmitStatuses.SUBMITTED
        recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/ingredient/{ingredient.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(pk=ingredient.pk).exists())
        self.assertTrue(Recipe.objects.filter(pk=recipe.pk).exists())


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestIngredientInventory(APITestCase):    
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.ingredient = Ingredient.objects.create(name="Ingredient", unit="kg", photo=media_utils.generate_test_image())
        self.ingredient2 = Ingredient.objects.create(name="Ingredient 2", unit="kg", photo=media_utils.generate_test_image())

    def tearDown(self):
        media_utils.delete_test_media()

    def test_add_ingredient_to_inventory(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/ingredient/inventory/{self.ingredient.pk}', 
            data={'amount': 2.5}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserIngredient.objects.filter(user=self.user, ingredient=self.ingredient).exists())
        user_ingredient = UserIngredient.objects.get(user=self.user, ingredient=self.ingredient)
        self.assertEqual(user_ingredient.amount, Decimal("2.5"))

    def test_update_ingredient_in_inventory(self):
        UserIngredient.objects.create(user=self.user, ingredient=self.ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/ingredient/inventory/{self.ingredient.pk}', 
            data={'amount': "1.5"}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_ingredient = UserIngredient.objects.get(user=self.user, ingredient=self.ingredient)
        self.assertEqual(user_ingredient.amount, Decimal("2.5"))

    def test_delete_ingredient_from_inventory(self):
        UserIngredient.objects.create(user=self.user, ingredient=self.ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.delete(f'/ingredient/inventory/{self.ingredient.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserIngredient.objects.filter(user=self.user, ingredient=self.ingredient).exists())

    def test_add_negative_amount_to_inventory(self):
        UserIngredient.objects.create(user=self.user, ingredient=self.ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/ingredient/inventory/{self.ingredient.pk}', 
            data={"amount": -0.6}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_ingredient = UserIngredient.objects.get(user=self.user, ingredient=self.ingredient)
        self.assertEqual(user_ingredient.amount, Decimal("0.4"))
        response: Response = self.client.post(
            f'/ingredient/inventory/{self.ingredient.pk}', 
            data={"amount": "-0.4"}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserIngredient.objects.filter(user=self.user, ingredient=self.ingredient).exists())

    @patch('recipeAPIapp.apps.Config.ContentLimits.inventory_limit', 1)
    def test_inventory_limit_exceeded(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/ingredient/inventory/{self.ingredient.pk}', 
            data={"amount": 0.50}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserIngredient.objects.filter(user=self.user, ingredient=self.ingredient).exists())
        response: Response = self.client.post(
            f'/ingredient/inventory/{self.ingredient2.pk}', 
            data={"amount": 0.50}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], {'non_field_errors': ['inventory limit exceeded.']})
        self.assertFalse(UserIngredient.objects.filter(user=self.user, ingredient=self.ingredient2).exists())

    def test_add_ingredient_unauthorized(self):
        response: Response = self.client.post(
            f'/ingredient/inventory/{self.ingredient.pk}', 
            data={'amount': 2.5}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        unverified_user = User.objects.create(email="unverified@example.com", name="Unverified User", vcode="NotNone")
        unverified_token = security.generate_token(unverified_user)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {unverified_token}'}
        response: Response = self.client.post(
            f'/ingredient/inventory/{self.ingredient.pk}', 
            data={'amount': 2.5}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(UserIngredient.objects.filter(user=unverified_user, ingredient=self.ingredient).exists())
