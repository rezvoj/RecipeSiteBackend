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


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
class TestRecipePhotoCUD(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.moderator = User.objects.create(email="moderator@example.com", name="Moderator", moderator=True)
        self.moderator_token = security.generate_token(self.moderator)
        self.recipe = Recipe.objects.create(
            name="Test Recipe", title="Test Recipe Title",
            user=self.user, prep_time=30, calories=200,
            submit_status=SubmitStatuses.SUBMITTED
        )

    def tearDown(self):
        media_utils.delete_test_media()

    def test_create_recipe_photo_with_number_adjustment(self):
        photo1 = RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=1)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/photo/{self.recipe.pk}',
            data={'photo': media_utils.generate_test_image(), 'number': 1},
            format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        photo1.refresh_from_db()
        self.assertEqual(photo1.number, 2)
        new_photo = RecipePhoto.objects.get(recipe=self.recipe, number=1)
        self.assertTrue(new_photo.photo)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)

    @patch('recipeAPIapp.apps.Config.PerRecipeLimits.photos', 2)
    def test_create_recipe_photo_limit_exceeded(self):
        RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=1)
        RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=2)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/photo/{self.recipe.pk}',
            data={'photo': media_utils.generate_test_image(), 'number': 3},
            format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'non_field_errors': ['photo limit exceeded.']}})

    def test_update_recipe_photo_with_number_adjustment(self):
        photos = [
            RecipePhoto.objects.create(
                recipe=self.recipe, number=idx,
                photo=media_utils.generate_test_image()
            ) for idx in range(1, 7)
        ]
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(
            f'/recipe/photo/{photos[0].pk}',
            data={'number': 4}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)
        for photo in photos:
            photo.refresh_from_db()
        for photo, position in zip(photos, [4, 1, 2, 3, 5, 6]):
            self.assertEqual(photo.number, position)
        response: Response = self.client.put(
            f'/recipe/photo/{photos[5].pk}',
            data={'number': 2}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for photo in photos:
            photo.refresh_from_db()
        for photo, position in zip(photos, [5, 1, 3, 4, 6, 2]):
            self.assertEqual(photo.number, position)

    def test_delete_recipe_photo_and_adjust_numbers(self):
        RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=1)
        photo2 = RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=2)
        photo3 = RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=3)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.delete(f'/recipe/photo/{photo2.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        photo3.refresh_from_db()
        self.assertEqual(photo3.number, 2)
        self.assertFalse(RecipePhoto.objects.filter(pk=photo2.pk).exists())
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)

    def test_create_recipe_photo_unauthorized(self):
        self.user.vcode = "NotNone"
        self.user.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/photo/{self.recipe.pk}',
            data={'photo': media_utils.generate_test_image(), 'number': 1},
            format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(RecipePhoto.objects.filter(recipe=self.recipe).exists())

    def test_update_recipe_photo_unauthorized(self):
        photo = RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=1)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(
            f'/recipe/photo/{photo.pk}',
            data={'number': 2}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        photo.refresh_from_db()
        self.assertEqual(photo.number, 1)

    def test_delete_recipe_photo_unauthorized(self):
        photo = RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=1)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/recipe/photo/{photo.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(RecipePhoto.objects.filter(pk=photo.pk).exists())


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
class TestRecipeInstructionCUD(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.moderator = User.objects.create(email="moderator@example.com", name="Moderator", moderator=True)
        self.moderator_token = security.generate_token(self.moderator)
        self.recipe = Recipe.objects.create(
            name="Test Recipe", title="Test Recipe Title",
            user=self.user, prep_time=30, calories=200,
            submit_status=SubmitStatuses.SUBMITTED
        )

    def tearDown(self):
        media_utils.delete_test_media()

    def test_create_recipe_instruction_with_number_adjustment(self):
        instruction1 = RecipeInstruction.objects.create(
            recipe=self.recipe, number=1, title="Instruction 01", 
            content="This is the content of instruction 01."
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/instruction/{self.recipe.pk}', data={
                'title': "Instruction 02", 'number': 1,
                'content': "This is the content of instruction 02."
            }, format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        instruction1.refresh_from_db()
        self.assertEqual(instruction1.number, 2)
        new_instruction = RecipeInstruction.objects.get(recipe=self.recipe, number=1)
        self.assertEqual(new_instruction.title, "Instruction 02")
        self.assertEqual(new_instruction.content, "This is the content of instruction 02.")
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)

    @patch('recipeAPIapp.apps.Config.PerRecipeLimits.instructions', 2)
    def test_create_recipe_instruction_limit_exceeded(self):
        RecipeInstruction.objects.create(
            recipe=self.recipe, number=1, title="Instruction 01", 
            content="This is the content of instruction 01."
        )
        RecipeInstruction.objects.create(
            recipe=self.recipe, number=2, title="Instruction 02", 
            content="This is the content of instruction 02."
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/instruction/{self.recipe.pk}', data={
                'title': "Instruction 03", 'number': 3, 
                'content': "This is the content of instruction 03."
            }, format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'non_field_errors': ['instruction limit exceeded.']}})

    def test_update_recipe_instruction_with_number_adjustment(self):
        instructions = [
            RecipeInstruction.objects.create(
                recipe=self.recipe, number=idx, title=f"Instruction {idx:02}", 
                content=f"This is the content of instruction {idx:02}."
            ) for idx in range(1, 7)
        ]
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(
            f'/recipe/instruction/{instructions[3].pk}',
            data={'number': 1}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)
        for instruction in instructions:
            instruction.refresh_from_db()
        for instruction, position in zip(instructions, [2, 3, 4, 1, 5, 6]):
            self.assertEqual(instruction.number, position)
        response: Response = self.client.put(
            f'/recipe/instruction/{instructions[0].pk}',
            data={'number': 5}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for instruction in instructions:
            instruction.refresh_from_db()
        for instruction, position in zip(instructions, [5, 2, 3, 1, 4, 6]):
            self.assertEqual(instruction.number, position)

    def test_delete_recipe_instruction_and_adjust_numbers(self):
        instruction1 = RecipeInstruction.objects.create(
            recipe=self.recipe, number=1, title="Instruction 01", 
            content="This is the content of instruction 01."
        )
        instruction2 = RecipeInstruction.objects.create(
            recipe=self.recipe, number=2, title="Instruction 02", 
            content="This is the content of instruction 02."
        )
        instruction3 = RecipeInstruction.objects.create(
            recipe=self.recipe, number=3, title="Instruction 03", 
            content="This is the content of instruction 03."
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.delete(f'/recipe/instruction/{instruction1.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        instruction2.refresh_from_db()
        instruction3.refresh_from_db()
        self.assertEqual(instruction2.number, 1)
        self.assertEqual(instruction3.number, 2)
        self.assertFalse(RecipeInstruction.objects.filter(pk=instruction1.pk).exists())
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)

    def test_create_recipe_instruction_unauthorized(self):
        self.user.vcode = "NotNone"
        self.user.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/instruction/{self.recipe.pk}', data={
                'title': "Instruction 01", 'number': 1, 
                'content': "This is the content of instruction 01."
            }, format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(RecipeInstruction.objects.filter(recipe=self.recipe).exists())

    def test_update_recipe_instruction_unauthorized(self):
        instruction = RecipeInstruction.objects.create(
            recipe=self.recipe, number=1, title="Instruction 01", 
            content="This is the content of instruction 01."
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(
            f'/recipe/instruction/{instruction.pk}',
            data={'number': 2}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        instruction.refresh_from_db()
        self.assertEqual(instruction.number, 1)

    def test_delete_recipe_instruction_unauthorized(self):
        instruction = RecipeInstruction.objects.create(
            recipe=self.recipe, number=1, title="Instruction 01", 
            content="This is the content of instruction 01."
        )
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/recipe/instruction/{instruction.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(RecipeInstruction.objects.filter(pk=instruction.pk).exists())


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
class TestRecipeIngredients(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.moderator = User.objects.create(email="moderator@example.com", name="Moderator", moderator=True)
        self.moderator_token = security.generate_token(self.moderator)
        self.recipe = Recipe.objects.create(
            name="Test Recipe", title="Test Recipe Title",
            user=self.user, prep_time=30, calories=200,
            submit_status=SubmitStatuses.SUBMITTED
        )
        self.ingredient = Ingredient.objects.create(name="Ingredient", unit="kg", photo=media_utils.generate_test_image())
        self.ingredient2 = Ingredient.objects.create(name="Ingredient 2", unit="kg", photo=media_utils.generate_test_image())

    def tearDown(self):
        media_utils.delete_test_media()

    def test_add_ingredient_to_recipe(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/ingredient/{self.recipe.pk}/{self.ingredient.pk}', 
            data={'amount': 4.27}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RecipeIngredient.objects.filter(recipe=self.recipe, ingredient=self.ingredient).exists())
        recipe_ingredient = RecipeIngredient.objects.get(recipe=self.recipe, ingredient=self.ingredient)
        self.assertEqual(recipe_ingredient.amount, Decimal("4.27"))
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)

    def test_update_ingredient_in_recipe(self):
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/ingredient/{self.recipe.pk}/{self.ingredient.pk}', 
            data={'amount': "0.75"}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe_ingredient = RecipeIngredient.objects.get(recipe=self.recipe, ingredient=self.ingredient)
        self.assertEqual(recipe_ingredient.amount, Decimal("1.75"))
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)

    def test_delete_ingredient_from_recipe(self):
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.delete(f'/recipe/ingredient/{self.recipe.pk}/{self.ingredient.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RecipeIngredient.objects.filter(recipe=self.recipe, ingredient=self.ingredient).exists())
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)

    def test_add_negative_amount_to_recipe(self):
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/ingredient/{self.recipe.pk}/{self.ingredient.pk}', 
            data={"amount": -0.7}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe_ingredient = RecipeIngredient.objects.get(recipe=self.recipe, ingredient=self.ingredient)
        self.assertEqual(recipe_ingredient.amount, Decimal("0.3"))
        response: Response = self.client.post(
            f'/recipe/ingredient/{self.recipe.pk}/{self.ingredient.pk}', 
            data={"amount": "-0.3"}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RecipeIngredient.objects.filter(recipe=self.recipe, ingredient=self.ingredient).exists())
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)

    @patch('recipeAPIapp.apps.Config.PerRecipeLimits.ingredients', 1)
    def test_recipe_ingredient_limit_exceeded(self):
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/ingredient/{self.recipe.pk}/{self.ingredient2.pk}', 
            data={"amount": 0.50}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], {'non_field_errors': ['ingredient limit exceeded.']})
        self.assertFalse(RecipeIngredient.objects.filter(recipe=self.recipe, ingredient=self.ingredient2).exists())

    def test_add_ingredient_to_recipe_unauthorized(self):
        self.user.vcode = "NotNone"
        self.user.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/recipe/ingredient/{self.recipe.pk}/{self.ingredient.pk}', 
            data={'amount': 1.0}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(RecipeIngredient.objects.filter(recipe=self.recipe).exists())

    def test_update_ingredient_in_recipe_unauthorized(self):
        recipe_ingredient = RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.post(
            f'/recipe/ingredient/{self.recipe.pk}/{self.ingredient.pk}', 
            data={'amount': 1.0}, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        recipe_ingredient.refresh_from_db()
        self.assertEqual(recipe_ingredient.amount, Decimal("1.0"))

    def test_delete_ingredient_from_recipe_unauthorized(self):
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/recipe/ingredient/{self.recipe.pk}/{self.ingredient.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(RecipeIngredient.objects.filter(recipe=self.recipe, ingredient=self.ingredient).exists())


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
class TestRecipeSubmission(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.moderator = User.objects.create(email="moderator@example.com", name="Moderator", moderator=True)
        self.moderator_token = security.generate_token(self.moderator)
        self.category = Category.objects.create(name="Test Category", photo=media_utils.generate_test_image())
        self.recipe = Recipe.objects.create(
            name="Test Recipe", title="Test Recipe Title",
            user=self.user, prep_time=30, calories=200,
            submit_status=SubmitStatuses.UNSUBMITTED
        )

    def tearDown(self):
        media_utils.delete_test_media()

    def test_successful_recipe_submission(self):
        self.recipe.categories.add(self.category)
        RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=1)
        RecipeInstruction.objects.create(recipe=self.recipe, number=1, title="Instruction", content="The content of the instruction.")
        ingredient = Ingredient.objects.create(name="Test Ingredient", unit="kg", photo=media_utils.generate_test_image())
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(f'/recipe/submit/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.SUBMITTED)

    def test_successful_recipe_submission_by_moderator(self):
        recipe_by_moderator = Recipe.objects.create(
            name="Moderator Recipe", title="Moderator Recipe Title",
            user=self.moderator, prep_time=30, calories=200,
            submit_status=SubmitStatuses.UNSUBMITTED
        )
        recipe_by_moderator.categories.add(self.category)
        ingredient = Ingredient.objects.create(name="Test Ingredient", unit="kg", photo=media_utils.generate_test_image())
        RecipePhoto.objects.create(recipe=recipe_by_moderator, photo=media_utils.generate_test_image(), number=1)
        RecipeInstruction.objects.create(recipe=recipe_by_moderator, number=1, title="Instruction", content="The content of the instruction.")
        RecipeIngredient.objects.create(recipe=recipe_by_moderator, ingredient=ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(f'/recipe/submit/{recipe_by_moderator.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe_by_moderator.refresh_from_db()
        self.assertEqual(recipe_by_moderator.submit_status, SubmitStatuses.ACCEPTED)

    def test_recipe_submission_with_missing_categories(self):
        RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=1)
        RecipeInstruction.objects.create(recipe=self.recipe, number=1, title="Instruction", content="The content of the instruction.")
        ingredient = Ingredient.objects.create(name="Test Ingredient", unit="kg", photo=media_utils.generate_test_image())
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(f'/recipe/submit/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'non_field_errors': ["categories can't be empty."]}})

    def test_recipe_submission_with_missing_photos(self):
        self.recipe.categories.add(self.category)
        RecipeInstruction.objects.create(recipe=self.recipe, number=1, title="Instruction", content="The content of the instruction.")
        ingredient = Ingredient.objects.create(name="Test Ingredient", unit="kg", photo=media_utils.generate_test_image())
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(f'/recipe/submit/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'non_field_errors': ["photos can't be empty."]}})

    def test_recipe_submission_with_missing_instructions(self):
        self.recipe.categories.add(self.category)
        RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=1)
        ingredient = Ingredient.objects.create(name="Test Ingredient", unit="kg", photo=media_utils.generate_test_image())
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=ingredient, amount=1.0)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(f'/recipe/submit/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'non_field_errors': ["instructions can't be empty."]}})

    def test_recipe_submission_with_missing_ingredients(self):
        self.recipe.categories.add(self.category)
        RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=1)
        RecipeInstruction.objects.create(recipe=self.recipe, number=1, title="Instruction", content="The content of the instruction.")
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(f'/recipe/submit/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'non_field_errors': ["ingredients can't be empty."]}})

    def test_recipe_submission_already_submitted(self):
        self.recipe.submit_status = SubmitStatuses.SUBMITTED
        self.recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(f'/recipe/submit/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recipe_submission_unauthorized(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(f'/recipe/submit/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)
        self.user.vcode = "NotNone"
        self.user.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(f'/recipe/submit/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.UNSUBMITTED)


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestRecipeAcceptOrDenyDecision(APITestCase):
    def setUp(self):
        self.moderator = User.objects.create(email="moderator@example.com", name="Moderator", moderator=True)
        self.moderator_token = security.generate_token(self.moderator)
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.recipe = Recipe.objects.create(
            name="Test Recipe", title="Test Recipe Title",
            user=self.user, prep_time=30, calories=200,
            submit_status=SubmitStatuses.SUBMITTED
        )

    def tearDown(self):
        media_utils.delete_test_media()

    def test_accept_recipe_as_moderator(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(f'/recipe/accept/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.ACCEPTED)

    def test_accept_recipe_unauthorized(self):
        response: Response = self.client.put(f'/recipe/accept/{self.recipe.pk}', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.SUBMITTED)

    def test_accept_already_accepted_recipe(self):
        self.recipe.submit_status = SubmitStatuses.ACCEPTED
        self.recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(f'/recipe/accept/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.ACCEPTED)

    def test_deny_recipe_as_moderator(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(
            f'/recipe/deny/{self.recipe.pk}',
            data={'deny_message': 'Recipe needs improvement.'},
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.DENIED)
        self.assertEqual(self.recipe.deny_message, 'Recipe needs improvement.')

    def test_deny_recipe_unauthorized(self):
        response: Response = self.client.put(
            f'/recipe/deny/{self.recipe.pk}',
            data={'deny_message': 'Recipe needs improvement.'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.SUBMITTED)

    def test_deny_already_accepted_recipe(self):
        self.recipe.submit_status = SubmitStatuses.ACCEPTED
        self.recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.put(
            f'/recipe/deny/{self.recipe.pk}',
            data={'deny_message': 'This should fail.'},
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.submit_status, SubmitStatuses.ACCEPTED)


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
class TestCookRecipe(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.ingredient1 = Ingredient.objects.create(name="Ingredient 1", unit="kg", photo=media_utils.generate_test_image())
        self.ingredient2 = Ingredient.objects.create(name="Ingredient 2", unit="g", photo=media_utils.generate_test_image())
        self.ingredient3 = Ingredient.objects.create(name="Ingredient 3", unit="mg", photo=media_utils.generate_test_image())
        self.ingredient4 = Ingredient.objects.create(name="Ingredient 4", unit="l", photo=media_utils.generate_test_image())
        UserIngredient.objects.create(user=self.user, ingredient=self.ingredient1, amount=Decimal('2.0'))
        UserIngredient.objects.create(user=self.user, ingredient=self.ingredient2, amount=Decimal('1.8'))
        UserIngredient.objects.create(user=self.user, ingredient=self.ingredient3, amount=Decimal('3.0'))
        UserIngredient.objects.create(user=self.user, ingredient=self.ingredient4, amount=Decimal('1.0'))
        self.recipe = Recipe.objects.create(
            name="Test Recipe", title="Test Recipe Title",
            user=self.user, prep_time=30, calories=200,
            submit_status=SubmitStatuses.ACCEPTED
        )
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient1, amount=Decimal('0.5'))
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient2, amount=Decimal('0.9'))
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient3, amount=Decimal('0.8'))

    def tearDown(self):
        media_utils.delete_test_media()

    def test_cook_recipe_successful(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/recipe/cook/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient1).amount, Decimal('1.5'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient2).amount, Decimal('0.9'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient3).amount, Decimal('2.2'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient4).amount, Decimal('1.0'))

    def test_cook_recipe_successful_with_servings(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/recipe/cook/{self.recipe.pk}', data={'servings': 2}, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient1).amount, Decimal('1.0'))
        self.assertFalse(UserIngredient.objects.filter(user=self.user, ingredient=self.ingredient2).exists())
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient3).amount, Decimal('1.4'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient4).amount, Decimal('1.0'))

    def test_cook_recipe_insufficient_ingredient(self):
        UserIngredient.objects.filter(user=self.user, ingredient=self.ingredient2).update(amount=Decimal('0.5'))
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/recipe/cook/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'non_field_errors': ['insufficient ingredients.']}})
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient1).amount, Decimal('2.0'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient2).amount, Decimal('0.5'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient3).amount, Decimal('3.0'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient4).amount, Decimal('1.0'))

    def test_cook_recipe_insufficient_ingredient_with_servings(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/recipe/cook/{self.recipe.pk}', data={'servings': 3}, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'non_field_errors': ['insufficient ingredients.']}})
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient1).amount, Decimal('2.0'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient2).amount, Decimal('1.8'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient3).amount, Decimal('3.0'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient4).amount, Decimal('1.0'))

    def test_cook_recipe_missing_ingredient(self):
        UserIngredient.objects.filter(user=self.user, ingredient=self.ingredient2).delete()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/recipe/cook/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'non_field_errors': ['insufficient ingredients.']}})
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient1).amount, Decimal('2.0'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient3).amount, Decimal('3.0'))
        self.assertEqual(UserIngredient.objects.get(user=self.user, ingredient=self.ingredient4).amount, Decimal('1.0'))

    def test_cook_recipe_unauthorized(self):
        self.user.vcode = "NotNone"
        self.user.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/recipe/cook/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
class TestRecipeFavour(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.recipe = Recipe.objects.create(
            name="Test Recipe", title="Test Recipe Title",
            user=self.user, prep_time=30, calories=200,
            submit_status=SubmitStatuses.ACCEPTED
        )
    
    def tearDown(self):
        media_utils.delete_test_media()
    
    def test_add_recipe_to_favourites(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/recipe/change-favourite/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.recipe.favoured_by.filter(pk=self.user.pk).exists())
    
    def test_remove_recipe_from_favourites(self):
        self.recipe.favoured_by.add(self.user)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/recipe/change-favourite/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.recipe.favoured_by.filter(pk=self.user.pk).exists())
    
    def test_favour_non_existent_recipe(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post('/recipe/change-favourite/999', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.recipe.submit_status = SubmitStatuses.UNSUBMITTED
        self.recipe.save()
        response: Response = self.client.post(f'/recipe/change-favourite/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_favour_recipe_unauthorized(self):
        response: Response = self.client.post(f'/recipe/change-favourite/{self.recipe.pk}', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        unverified_user = User.objects.create(email="unverified@example.com", name="Unverified User", vcode="NotNone")
        unverified_token = security.generate_token(unverified_user)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {unverified_token}'}
        response: Response = self.client.post(f'/recipe/change-favourite/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestRecipeDetail(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.moderator = User.objects.create(email="moderator@example.com", name="Moderator", moderator=True)
        self.moderator_token = security.generate_token(self.moderator)
        self.other_user = User.objects.create(email="other_user@example.com", name="Other User")
        self.other_user_token = security.generate_token(self.other_user)
        self.category1 = Category.objects.create(name="Category1", photo=media_utils.generate_test_image())
        self.category2 = Category.objects.create(name="Category2", photo=media_utils.generate_test_image())
        self.ingredient1 = Ingredient.objects.create(name="Ingredient", unit="kg", photo=media_utils.generate_test_image())
        self.ingredient2 = Ingredient.objects.create(name="Ingredient2", unit="g", photo=media_utils.generate_test_image())
        self.recipe = Recipe.objects.create(
            name="Test Recipe", title="Test Recipe Title",
            user=self.user, prep_time=30, calories=200,
            submit_status=SubmitStatuses.ACCEPTED
        )
        self.recipe.categories.add(self.category1, self.category2)
        self.recipe.favoured_by.add(self.user, self.moderator)
        UserIngredient.objects.create(user=self.user, ingredient=self.ingredient1, amount=3.0)
        UserIngredient.objects.create(user=self.user, ingredient=self.ingredient2, amount=1.1)
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient1, amount=1.5)
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient2, amount=0.5)
        self.photo1 = RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=2)
        self.photo2 = RecipePhoto.objects.create(recipe=self.recipe, photo=media_utils.generate_test_image(), number=1)
        self.instruction1 = RecipeInstruction.objects.create(
            recipe=self.recipe, title="Instruction 3", content="Step 3", 
            number=3, photo=media_utils.generate_test_image()
        )
        self.instruction2 = RecipeInstruction.objects.create(
            recipe=self.recipe, title="Instruction 1", content="Step 1",
            number=1, photo=media_utils.generate_test_image()
        )
        self.instruction3 = RecipeInstruction.objects.create(recipe=self.recipe, title="Instruction 2", content="Step 2", number=2)
        self.rating1 = Rating.objects.create(user=self.other_user, recipe=self.recipe, stars=4, content="Good recipe!")
        self.rating2 = Rating.objects.create(user=self.user, recipe=self.recipe, stars=2, content="Good recipe2!")

    def tearDown(self):
        media_utils.delete_test_media()

    def test_get_recipe_detail_success(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.get(f'/recipe/detail/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'id': self.recipe.pk, 
            'photo': self.photo2.photo.url,
            'user': {
                'id': self.user.pk, 
                'photo': None, 'name': 'Regular User', 
                'created_at': self.user.created_at.isoformat()
            }, 
            'name': 'Test Recipe', 'title': 'Test Recipe Title', 
            'prep_time': 30, 'calories': 200, 
            'created_at': self.recipe.created_at.isoformat(), 
            'submit_status': 'ACCEPTED', 
            'deny_message': None,
            'rating_count': 2, 'avg_rating': 3.0,
            'favoured': True, 'cookable_portions': 2,
            'favoured_count': 2, 'categories': [
                {
                    'id': self.category1.pk, 
                    'photo': self.category1.photo.url, 
                    'name': 'Category1'
                }, {
                    'id': self.category2.pk, 
                    'photo': self.category2.photo.url, 
                    'name': 'Category2'
                }
            ], 
            'ingredients': [
                {
                    'ingredient': {
                        'id': self.ingredient1.pk, 
                        'photo': self.ingredient1.photo.url, 
                        'unit': 'kg', 'name': 'Ingredient'
                    }, 
                    'amount': '1.50'
                }, {
                    'ingredient': {
                        'id': self.ingredient2.pk, 
                        'photo': self.ingredient2.photo.url, 
                        'unit': 'g', 'name': 'Ingredient2'
                    }, 
                    'amount': '0.50'
                }
            ],
            'photos': [
                {'id': self.photo2.pk, 'photo': self.photo2.photo.url}, 
                {'id': self.photo1.pk, 'photo': self.photo1.photo.url}
            ], 
            'instructions': [
                {
                    'id': self.instruction2.pk, 
                    'photo': self.instruction2.photo.url, 
                    'title': 'Instruction 1', 'content': 'Step 1'
                }, {
                    'id': self.instruction3.pk, 'photo': None, 
                    'title': 'Instruction 2', 'content': 'Step 2'
                }, {
                    'id': self.instruction1.pk, 
                    'photo': self.instruction1.photo.url, 
                    'title': 'Instruction 3', 'content': 'Step 3'
                }
            ]
        })

    def test_get_recipe_detail_as_other_user_denied_access(self):
        self.recipe.submit_status = SubmitStatuses.UNSUBMITTED
        self.recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.other_user_token}'}
        response: Response = self.client.get(f'/recipe/detail/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_recipe_detail_as_moderator_success(self):
        self.recipe.submit_status = SubmitStatuses.SUBMITTED
        self.recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.get(f'/recipe/detail/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_recipe_detail_as_moderator_denied_access(self):
        self.recipe.submit_status = SubmitStatuses.DENIED
        self.recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.get(f'/recipe/detail/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_recipe_detail_as_admin_success(self):
        self.recipe.submit_status = SubmitStatuses.SUBMITTED
        self.recipe.save()
        headers = {'HTTP_ADMINCODE': 'TEST_ADMIN_CODE'}
        response: Response = self.client.get(f'/recipe/detail/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_recipe_detail_as_owner_success_for_denied_recipe(self):
        self.recipe.submit_status = SubmitStatuses.DENIED
        self.recipe.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.get(f'/recipe/detail/{self.recipe.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_recipe_detail_unauthorized(self):
        response: Response = self.client.get(f'/recipe/detail/{self.recipe.pk}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['favoured'])
        self.assertIsNone(response.data['cookable_portions'])


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
class TestRatingCUD(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.other_user = User.objects.create(email="other_user@example.com", name="Other User")
        self.other_user_token = security.generate_token(self.other_user)
        self.recipe = Recipe.objects.create(
            name="Test Recipe", title="Test Recipe Title",
            user=self.user, prep_time=30, calories=200,
            submit_status=SubmitStatuses.ACCEPTED
        )

    def tearDown(self):
        media_utils.delete_test_media()

    def test_create_rating_successful(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/rating/{self.recipe.pk}',
            data={'stars': 4, 'content': 'Great recipe!'},
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        rating = Rating.objects.get(pk=response.data['id'])
        self.assertEqual(rating.stars, 4)
        self.assertEqual(rating.content, 'Great recipe!')
        self.assertEqual(rating.user, self.user)
        self.assertIsNone(rating.edited_at)

    @patch('recipeAPIapp.apps.Config.ContentLimits.rating', (0, 24))
    def test_create_rating_limit_exceeded(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/rating/{self.recipe.pk}',
            data={'stars': 4, 'content': 'Great recipe!'},
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'limit': 0, 'hours': 24}})

    def test_create_rating_recipe_already_rated(self):
        Rating.objects.create(user=self.user, recipe=self.recipe, stars=5, content="Already rated!")
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/rating/{self.recipe.pk}',
            data={'stars': 4, 'content': 'Great recipe!'},
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': {'non_field_errors': ['recipe already rated.']}})

    def test_update_rating_successful(self):
        rating = Rating.objects.create(user=self.user, recipe=self.recipe, stars=4, content="Great recipe!")
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.put(
            f'/rating/{rating.pk}',
            data={'stars': 5, 'content': 'Updated review!'},
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rating.refresh_from_db()
        self.assertEqual(rating.stars, 5)
        self.assertEqual(rating.content, 'Updated review!')
        self.assertIsNotNone(rating.edited_at)
        self.assertAlmostEqual(rating.edited_at, utc_now(), delta=timedelta(seconds=1))

    def test_delete_rating_successful(self):
        rating = Rating.objects.create(user=self.user, recipe=self.recipe, stars=4, content="Great recipe!")
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.delete(f'/rating/{rating.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Rating.objects.filter(pk=rating.pk).exists())

    def test_create_rating_unauthorized(self):
        self.user.vcode = "NotNone"
        self.user.save()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(
            f'/rating/{self.recipe.pk}',
            data={'stars': 4, 'content': 'Great recipe!'},
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Rating.objects.filter(recipe=self.recipe, user=self.user).exists())

    def test_update_rating_unauthorized(self):
        rating = Rating.objects.create(user=self.user, recipe=self.recipe, stars=4, content="Great recipe!")
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.other_user_token}'}
        response: Response = self.client.put(
            f'/rating/{rating.pk}',
            data={'stars': 5, 'content': 'Unauthorized update!'},
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        rating.refresh_from_db()
        self.assertNotEqual(rating.stars, 5)
        self.assertNotEqual(rating.content, 'Unauthorized update!')
        self.assertIsNone(rating.edited_at)

    def test_delete_rating_unauthorized(self):
        rating = Rating.objects.create(user=self.user, recipe=self.recipe, stars=4, content="Great recipe!")
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.other_user_token}'}
        response: Response = self.client.delete(f'/rating/{rating.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Rating.objects.filter(pk=rating.pk).exists())


@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
class TestRatingLike(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.user)
        self.recipe = Recipe.objects.create(
            name="Test Recipe", title="Test Recipe Title",
            user=self.user, prep_time=30, calories=200,
            submit_status=SubmitStatuses.ACCEPTED
        )
        self.rating = Rating.objects.create(
            user=self.user, recipe=self.recipe, 
            stars=4, content="Great recipe!"
        )
    
    def tearDown(self):
        media_utils.delete_test_media()

    def test_add_rating_to_liked(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/rating/change-liked/{self.rating.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.rating.liked_by.filter(pk=self.user.pk).exists())

    def test_remove_rating_from_liked(self):
        self.rating.liked_by.add(self.user)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post(f'/rating/change-liked/{self.rating.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.rating.liked_by.filter(pk=self.user.pk).exists())

    def test_like_non_existent_rating(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        response: Response = self.client.post('/rating/change-liked/999', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.recipe.submit_status = SubmitStatuses.UNSUBMITTED
        self.recipe.save()
        response: Response = self.client.post(f'/rating/change-liked/{self.rating.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_like_rating_unauthorized(self):
        response: Response = self.client.post(f'/rating/change-liked/{self.rating.pk}', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
