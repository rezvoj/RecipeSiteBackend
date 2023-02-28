from datetime import timedelta
from django.test import override_settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
import recipeAPIapp.utils.security as security
import recipeAPIapp.tests.media_utils as media_utils
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.models.user import User, UserReport
from recipeAPIapp.models.recipe import Recipe, Rating, SubmitStatuses, RecipeIngredient, RecipePhoto
from recipeAPIapp.models.categorical import Category, Ingredient, UserIngredient



@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestUserFilter(APITestCase):    
    
    def setUp(self):
        self.regular_user = User.objects.create(email="regular_user@example.com", name="Regular User")
        self.user_token = security.generate_token(self.regular_user)

        """ User 1: Alice, reports: 0, recipes: 4 (1 new), ratings: 4, 
            avg_rating: 4.25, photo: yes, moderator: no """
        self.alice = User.objects.create(
            email="alice@example.com", name="Alice", 
            moderator=False, photo=media_utils.generate_test_image()
        )
        recipe1 = Recipe.objects.create(
            user=self.alice, name="Alice's Pie", title="Delicious Pie", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=60, calories=300,
            created_at=utc_now() - timedelta(days=10)
        )
        recipe2 = Recipe.objects.create(
            user=self.alice, name="Alice's Soup", title="Healthy Soup", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=30, calories=150,
            created_at=utc_now() - timedelta(days=10)
        )
        recipe3 = Recipe.objects.create(
            user=self.alice, name="Alice's Bread", title="Homemade Bread", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=120, calories=200, 
            created_at=utc_now() - timedelta(days=10)
        )
        recipe4 = Recipe.objects.create(
            user=self.alice, name="Alice's Salad", title="Fresh Salad", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=15, calories=100
        )
        Rating.objects.create(user=self.alice, recipe=recipe1, stars=5)
        Rating.objects.create(user=self.alice, recipe=recipe2, stars=4)
        Rating.objects.create(user=self.alice, recipe=recipe3, stars=4)
        Rating.objects.create(user=self.alice, recipe=recipe4, stars=4)
        
        """ User 2: Bob, reports: 0, recipes: 2 (1 new), ratings: 2, 
            avg_rating: 3.5, photo: no, moderator: yes """
        self.bob = User.objects.create(
            email="bob@example.com", name="Bob", 
            moderator=True
        )
        self.moderator_token = security.generate_token(self.bob)
        recipe1 = Recipe.objects.create(
            user=self.bob, name="Bob's Burger", title="Tasty Burger", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=20, calories=500
        )
        recipe2 = Recipe.objects.create(
            user=self.bob, name="Bob's Fries", title="Crispy Fries", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=25, calories=300, 
            created_at=utc_now() - timedelta(days=10)
        )
        Rating.objects.create(user=self.bob, recipe=recipe1, stars=4)
        Rating.objects.create(user=self.bob, recipe=recipe2, stars=3)
        
        """ User 3: Charlie, reports: 0, recipes: 3 (2 new), ratings: 3, 
            avg_rating: 2.67, photo: yes, moderator: no """
        self.charlie = User.objects.create(
            email="charlie@example.com", name="Charlie", 
            moderator=False, photo=media_utils.generate_test_image()
        )
        recipe1 = Recipe.objects.create(
            user=self.charlie, name="Charlie's Salad", title="Simple Salad", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=10, calories=100
        )
        recipe2 = Recipe.objects.create(
            user=self.charlie, name="Charlie's Sandwich", title="Quick Sandwich", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=5, calories=150, 
            created_at=utc_now() - timedelta(days=10)
        )
        recipe3 = Recipe.objects.create(
            user=self.charlie, name="Charlie's Soup", title="Warm Soup", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=30, calories=200
        )
        Rating.objects.create(user=self.charlie, recipe=recipe1, stars=2)
        Rating.objects.create(user=self.charlie, recipe=recipe2, stars=3)
        Rating.objects.create(user=self.charlie, recipe=recipe3, stars=3)
        
        """ User 4: Diana, reports: 2, recipes: 0, ratings: 0, 
            avg_rating: 0.0, photo: no, moderator: yes """ 
        self.diana = User.objects.create(
            email="diana@example.com", name="Diana", 
            moderator=True
        )
        UserReport.objects.create(user=self.alice, reported=self.diana)
        UserReport.objects.create(user=self.charlie, reported=self.diana)

        """ User 5: Eve, reports: 0, recipes: 4 (1 new), ratings: 4, 
            avg_rating: 4.25, photo: yes, moderator: no """ 
        self.eve = User.objects.create(
            email="eve@example.com", name="Eve", 
            moderator=False, photo=media_utils.generate_test_image()
        )
        recipe1 = Recipe.objects.create(
            user=self.eve, name="Eve's Cake", title="Chocolate Cake", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=90, calories=400
        )
        recipe2 = Recipe.objects.create(
            user=self.eve, name="Eve's Pasta", title="Italian Pasta", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=40, calories=250,
            created_at=utc_now() - timedelta(days=10)
        )
        recipe3 = Recipe.objects.create(
            user=self.eve, name="Eve's Ice Cream", title="Vanilla Ice Cream", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=15, calories=200,
            created_at=utc_now() - timedelta(days=10)
        )
        recipe4 = Recipe.objects.create(
            user=self.eve, name="Eve's Smoothie", title="Fruit Smoothie", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=10, calories=150, 
            created_at=utc_now() - timedelta(days=10)
        )
        Rating.objects.create(user=self.eve, recipe=recipe1, stars=4)
        Rating.objects.create(user=self.eve, recipe=recipe2, stars=5)
        Rating.objects.create(user=self.eve, recipe=recipe3, stars=3)
        Rating.objects.create(user=self.eve, recipe=recipe4, stars=5)

        """ User 6: Frank, reports: 0, recipes: 2 (1 new), ratings: 2, 
            avg_rating: 2.0, photo: no, moderator: no """
        self.frank = User.objects.create(
            email="frank@example.com", name="Frank", 
            moderator=False
        )
        recipe1 = Recipe.objects.create(
            user=self.frank, name="Frank's Pizza", title="Homemade Pizza", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=60, calories=600
        )
        recipe2 = Recipe.objects.create(
            user=self.frank, name="Frank's Pasta", title="Simple Pasta", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=20, calories=200, 
            created_at=utc_now() - timedelta(days=10)
        )
        Rating.objects.create(user=self.frank, recipe=recipe1, stars=1)
        Rating.objects.create(user=self.frank, recipe=recipe2, stars=3)

        """ User 7: Grace, reports: 0, recipes: 2 (2 new), ratings: 2, 
            avg_rating: 5.0, photo: yes, moderator: yes """
        self.grace = User.objects.create(
            email="grace@example.com", name="Grace", 
            moderator=True, photo=media_utils.generate_test_image()
        )
        recipe1 = Recipe.objects.create(
            user=self.grace, name="Grace's Pancakes", title="Fluffy Pancakes", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=20, calories=300
        )
        recipe2 = Recipe.objects.create(
            user=self.grace, name="Grace's Smoothie", title="Fruit Smoothie", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=10, calories=150
        )
        Rating.objects.create(user=self.grace, recipe=recipe1, stars=5)
        Rating.objects.create(user=self.grace, recipe=recipe2, stars=5)

        """ User 8: Henry, banned: yes, recipes: 1 (0 new), ratings: 1, 
            avg_rating: 4.0, photo: yes, moderator: no, BANNED """
        self.henry = User.objects.create(
            email="henry@example.com", name="Henry", 
            banned=True, photo=media_utils.generate_test_image()
        )
        recipe1 = Recipe.objects.create(
            user=self.henry, name="Henry's Cake", title="Chocolate Cake", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=90, calories=400, 
            created_at=utc_now() - timedelta(days=10)
        )
        Rating.objects.create(user=self.henry, recipe=recipe1, stars=4)

        """ User 9: Isabel, reports: 1, recipes: 0, ratings: 0, 
            avg_rating: 0.0, photo: no, moderator: no """
        self.isabel = User.objects.create(
            email="isabel@example.com", name="Isabel", 
            moderator=False
        )
        UserReport.objects.create(user=self.grace, reported=self.isabel)

        """ User 10: Jack, reports: 0, recipes: 3 (2 new), ratings: 3, 
            avg_rating: 4.33, photo: no, moderator: yes """
        self.jack = User.objects.create(
            email="jack@example.com", name="Jack", 
            moderator=True
        )
        recipe1 = Recipe.objects.create(
            user=self.jack, name="Jack's Tacos", title="Spicy Tacos", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=30, calories=400
        )
        recipe2 = Recipe.objects.create(
            user=self.jack, name="Jack's Steak", title="Grilled Steak", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=50, calories=500
        )
        recipe3 = Recipe.objects.create(
            user=self.jack, name="Jack's Salad", title="Fresh Salad", 
            submit_status=SubmitStatuses.ACCEPTED, prep_time=15, calories=150, 
            created_at=utc_now() - timedelta(days=10)
        )
        Rating.objects.create(user=self.jack, recipe=recipe1, stars=4)
        Rating.objects.create(user=self.jack, recipe=recipe2, stars=5)
        Rating.objects.create(user=self.jack, recipe=recipe3, stars=4)


    def tearDown(self):
        media_utils.delete_test_media()


    def test_regular_user_filter(self):
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.user_token}"}
        params = {
            'search_string': 'a c',
            'order_by': ['-avg_rating', 'name'],
            'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/user/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(response.data['results'][0]['id'], self.grace.pk)
        self.assertEqual(response.data['results'][1]['id'], self.alice.pk)
        self.assertEqual(response.data['results'][2]['id'], self.jack.pk)
        self.assertEqual(response.data['results'][3]['id'], self.charlie.pk)
        expected_grace_data = {
            'id': self.grace.pk, 'name': 'Grace',
            'photo': self.grace.photo.url,
            'created_at': self.grace.created_at.isoformat(), 
            'rating_count': 2, 'recipe_count': 2, 'avg_rating': 5.0
        }
        self.assertEqual(response.data['results'][0], expected_grace_data)


    def test_regular_user_report_count_filter(self):
        headers = {'HTTP_AUTHORIZATION': self.user_token}
        params = {
            'order_by': ['-report_count'],
            'page': 1, 'page_size': 2
        }
        response: Response = self.client.get(f'/user/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], {'order_by': ['invalid ordering parameters.']})


    def test_admin_filter(self):
        headers = {'HTTP_ADMINCODE': 'TEST_ADMIN_CODE'}
        params = {
            'moderator': True,
            'order_by': ['-recipe_count', '-name'],
            'page': 2, 'page_size': 2
        }
        response: Response = self.client.get(f'/user/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 2)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['id'], self.bob.pk)
        self.assertEqual(response.data['results'][1]['id'], self.diana.pk)
        self.assertEqual(response.data['results'][0]['moderator'], True)
        self.assertEqual(response.data['results'][1]['moderator'], True)
        self.assertEqual(response.data['results'][0]['report_count'], 0)
        self.assertEqual(response.data['results'][1]['report_count'], 2)


    def test_moderator_filter(self):
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.moderator_token}"}
        params = {
            'moderator': True,
            'order_by': ['-report_count', '-recipe_count', 'name'],
            'order_time_window': 5,
            'page': 1, 'page_size': 3
        }
        response: Response = self.client.get(f'/user/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['count'], 10)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['results'][0]['id'], self.diana.pk)
        self.assertEqual(response.data['results'][1]['id'], self.isabel.pk)
        self.assertEqual(response.data['results'][2]['id'], self.charlie.pk)
        self.assertEqual(response.data['results'][0]['moderator'], True)
        self.assertEqual(response.data['results'][0]['report_count'], 2)



@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestCategoryFilter(APITestCase): 
    
    def setUp(self):
        self.test_user = User.objects.create(email="testuser@example.com", name="Test User")
        self.user_token = security.generate_token(self.test_user)
        self.other_user = User.objects.create(email="testuser2@example.com", name="Test User2")

        """ Category 1: Main Appetizers, favoured: yes, recipes: 2 (2 new) (1 (1 new) by test user)"""
        self.appetizers = Category.objects.create(
            name="Main Appetizers", about="Starters and light bites", 
            photo=media_utils.generate_test_image()
        )
        self.appetizers.favoured_by.add(self.test_user)
        self.appetizers.save()
        recipe1 = Recipe.objects.create(
            user=self.test_user, name="Bruschetta", title="Italian Bruschetta",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=15, calories=200
        )
        recipe1.categories.add(self.appetizers)
        recipe1.save()
        recipe2 = Recipe.objects.create(
            user=self.other_user, name="Stuffed Mushrooms", title="Cheesy Stuffed Mushrooms",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=25, calories=150
        )
        recipe2.categories.add(self.appetizers)
        recipe2.save()

        """ Category 2: Main Courses, favoured: no, recipes: 3 (1 new) (1 (1 new) by test user) """
        self.main_courses = Category.objects.create(
            name="Main Courses", about="Hearty and filling dishes", 
            photo=media_utils.generate_test_image()
        )
        recipe1 = Recipe.objects.create(
            user=self.test_user, name="Grilled Chicken", title="Juicy Grilled Chicken",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=60, calories=400
        )
        recipe1.categories.add(self.main_courses)
        recipe1.save()
        recipe2 = Recipe.objects.create(
            user=self.other_user, name="Steak and Potatoes", title="Classic Steak and Potatoes",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=90, calories=600,
            created_at=utc_now() - timedelta(days=10)
        )
        recipe2.categories.add(self.main_courses)
        recipe2.save()
        recipe3 = Recipe.objects.create(
            user=self.other_user, name="Vegetarian Lasagna", title="Healthy Vegetarian Lasagna",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=120, calories=450,
            created_at=utc_now() - timedelta(days=10)
        )
        recipe3.categories.add(self.main_courses)
        recipe3.save()

        """ Category 3: Desserts, favoured: yes, recipes: 1 (0 new) (0 by test user)"""
        self.desserts = Category.objects.create(
            name="Desserts", about="Sweet and delightful treats", 
            photo=media_utils.generate_test_image()
        )
        self.desserts.favoured_by.add(self.test_user)
        self.desserts.save()
        recipe1 = Recipe.objects.create(
            user=self.other_user, name="Chocolate Cake", title="Rich Chocolate Cake",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=90, calories=500,
            created_at=utc_now() - timedelta(days=10)
        )
        recipe1.categories.add(self.desserts)
        recipe1.save()

        """ Category 4: Main Salads, favoured: no, recipes: 2 (0 new) (2 by test user)"""
        self.salads = Category.objects.create(
            name="Main Salads", about="Fresh and healthy salads"
        )
        recipe1 = Recipe.objects.create(
            user=self.test_user, name="Caesar Salad", title="Classic Caesar Salad",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=20, calories=300,
            created_at=utc_now() - timedelta(days=10)
        )
        recipe1.categories.add(self.salads)
        recipe1.save()
        recipe2 = Recipe.objects.create(
            user=self.test_user, name="Greek Salad", title="Authentic Greek Salad",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=15, calories=250,
            created_at=utc_now() - timedelta(days=10)
        )
        recipe2.categories.add(self.salads)
        recipe2.save()

        """ Category 5: Soups, favoured: yes, recipes: 0 """
        self.soups = Category.objects.create(
            name="Soups", about="Warm and comforting soups", 
            photo=media_utils.generate_test_image()
        )
        self.soups.favoured_by.add(self.test_user)
        self.soups.save()


    def tearDown(self):
        media_utils.delete_test_media()


    def test_user_filter(self):
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.user_token}"}
        params = {
            'favoured': True,
            'order_by': ['-self_recipe_count', '-name'],
            'page': 1, 'page_size': 2
        }
        response: Response = self.client.get(f'/category/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 2)
        expected_appetizers = {
            'id': self.appetizers.pk, 'name': "Main Appetizers",
            'photo': self.appetizers.photo.url, 
            'about': "Starters and light bites", 
            'recipe_count': 2, 'self_recipe_count': 1, 'favoured': True
        }
        self.assertEqual(response.data['results'][0], expected_appetizers)
        self.assertEqual(response.data['results'][1]['id'], self.soups.pk)
        params['page'] = 2
        response: Response = self.client.get(f'/category/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 2)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.desserts.pk)


    def test_anon_filter(self):
        headers = {}
        params = {
            'search_string': 'main',
            'favoured': True, 'order_time_window': 5,
            'order_by': ['-recipe_count', 'name'],
            'page': 1, 'page_size': 4
        }
        response: Response = self.client.get(f'/category/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['id'], self.appetizers.pk)
        self.assertEqual(response.data['results'][0]['self_recipe_count'], 0)
        self.assertEqual(response.data['results'][0]['favoured'], None)
        self.assertEqual(response.data['results'][1]['id'], self.main_courses.pk)
        self.assertEqual(response.data['results'][2]['id'], self.salads.pk)



@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestIngredientFilter(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create(email="testuser@example.com", name="Test User")
        self.user_token = security.generate_token(self.test_user)
        self.other_user = User.objects.create(email="testuser2@example.com", name="Test User2")
        self.recipe1 = Recipe.objects.create(
            user=self.test_user, name="Tomato Soup", title="Delicious Tomato Soup",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=30, calories=150
        )
        self.recipe2 = Recipe.objects.create(
            user=self.test_user, name="Cheese Pizza", title="Homemade Cheese Pizza",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=60, calories=400,
            created_at=utc_now() - timedelta(days=10)
        )
        self.recipe3 = Recipe.objects.create(
            user=self.other_user, name="Caprese Salad", title="Caprese Salad with Basil",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=10, calories=200
        )
        self.recipe4 = Recipe.objects.create(
            user=self.other_user, name="Grilled Chicken", title="Juicy Grilled Chicken",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=60, calories=400,
            created_at=utc_now() - timedelta(days=10)
        )

        """ Ingredient 1: Tomato, used in 1 recipe (1 new) (1 test_user), owned """
        self.tomato = Ingredient.objects.create(
            name="Tomato", unit="kg", about="Fresh tomatoes", 
            photo=media_utils.generate_test_image()
        )
        RecipeIngredient.objects.create(recipe=self.recipe1, ingredient=self.tomato, amount=0.5)
        UserIngredient.objects.create(user=self.test_user, ingredient=self.tomato, amount=1.0)

        """ Ingredient 2: Cheese, used in 2 recipes (1 new) (2 test_user), owned """
        self.cheese = Ingredient.objects.create(
            name="Cheese", unit="kg", about="Creamy cheese", 
            photo=media_utils.generate_test_image()
        )
        RecipeIngredient.objects.create(recipe=self.recipe1, ingredient=self.cheese, amount=0.5)
        RecipeIngredient.objects.create(recipe=self.recipe2, ingredient=self.cheese, amount=0.4)
        UserIngredient.objects.create(user=self.test_user, ingredient=self.cheese, amount=0.6)

        """ Ingredient 3: Basil, used in 2 recipes (2 new) (1 test_user) """
        self.basil = Ingredient.objects.create(
            name="Basil", unit="g", about="Fresh basil leaves", 
            photo=media_utils.generate_test_image()
        )
        RecipeIngredient.objects.create(recipe=self.recipe1, ingredient=self.basil, amount=0.05)
        RecipeIngredient.objects.create(recipe=self.recipe3, ingredient=self.basil, amount=0.1)
        UserIngredient.objects.create(user=self.other_user, ingredient=self.basil, amount=0.2)

        """ Ingredient 4: Garlic, used in 2 recipes (1 new) (2 test_user) """
        self.garlic = Ingredient.objects.create(
            name="Garlic", unit="cloves", about="Fresh garlic", 
            photo=media_utils.generate_test_image()
        )
        RecipeIngredient.objects.create(recipe=self.recipe1, ingredient=self.garlic, amount=2.0)
        RecipeIngredient.objects.create(recipe=self.recipe2, ingredient=self.garlic, amount=1.0)

        """ Ingredient 5: Onion, used in 1 recipe (0 new) (0 test_user), owned """
        self.onion = Ingredient.objects.create(
            name="Onion", unit="kg", about="Fresh onions", 
            photo=media_utils.generate_test_image()
        )
        RecipeIngredient.objects.create(recipe=self.recipe4, ingredient=self.onion, amount=0.8)
        UserIngredient.objects.create(user=self.test_user, ingredient=self.onion, amount=2.0)


    def tearDown(self):
        media_utils.delete_test_media()

    
    def test_user_filter(self):
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.user_token}"}
        params = {
            'owned': True,
            'used': True,
            'order_by': ['-self_recipe_count', '-name'],
            'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/ingredient/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        expected_cheese = {
            'id': self.cheese.pk, 'name': 'Cheese',
            'photo': self.cheese.photo.url, 
            'unit': 'kg', 'about': 'Creamy cheese', 
            'recipe_count': 2, 'self_recipe_count': 2, 
            'self_amount': '0.60'
        }
        self.assertEqual(response.data['results'][0], expected_cheese)
        self.assertEqual(response.data['results'][1]['id'], self.tomato.pk)


    def test_anon_filter(self):
        headers = {}
        params = {
            'owned': True, 'order_time_window': 5,
            'order_by': ['-recipe_count', 'name'],
            'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/ingredient/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        self.assertEqual(response.data['results'][0]['id'], self.basil.pk)
        self.assertEqual(response.data['results'][1]['id'], self.cheese.pk)
        self.assertEqual(response.data['results'][2]['id'], self.garlic.pk)
        self.assertEqual(response.data['results'][3]['id'], self.tomato.pk)
        self.assertEqual(response.data['results'][4]['id'], self.onion.pk)
        params = {'search_string': "tomato", 'page': 1, 'page_size': 5}
        response: Response = self.client.get(f'/ingredient/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.tomato.pk)



@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestRatingFilter(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create(email="user1@example.com", name="User One")
        self.user_token = security.generate_token(self.user1)
        self.user2 = User.objects.create(email="user2@example.com", name="User Two")
        self.user3 = User.objects.create(email="user3@example.com", name="User Three")
        self.user4 = User.objects.create(email="user4@example.com", name="User Four")
        self.recipe1 = Recipe.objects.create(
            user=self.user1, name="Pancakes", title="Fluffy Pancakes",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=20, calories=300
        )
        self.recipe2 = Recipe.objects.create(
            user=self.user2, name="Smoothie", title="Fruit Smoothie",
            submit_status=SubmitStatuses.ACCEPTED, prep_time=10, calories=150
        )

        """ Rating 1: 5 stars, content with 'great', has photo, by 2, 4 likes (1, 2, 3, 4) """
        self.rating1 = Rating.objects.create(
            user=self.user2, recipe=self.recipe1, stars=5, 
            content="Great pancakes, very fluffy and tasty!", 
            photo=media_utils.generate_test_image(),
            created_at=utc_now() - timedelta(days=2)
        )
        self.rating1.liked_by.add(self.user1, self.user2, self.user3, self.user4)

        """ Rating 2: 4 stars, no content, no photo, by 3, 0 likes """
        self.rating2 = Rating.objects.create(
            user=self.user3, recipe=self.recipe1, stars=4,
            created_at=utc_now() - timedelta(days=4)
        )

        """ Rating 3: 3 stars, content with 'good', no photo, by 4, 1 like (1) """
        self.rating3 = Rating.objects.create(
            user=self.user4, recipe=self.recipe1, stars=3, 
            content="Good, but could use more flavor.", 
            created_at=utc_now() - timedelta(days=6)
        )
        self.rating3.liked_by.add(self.user1)

        """ Rating 4: 5 stars, content with 'excellent', has photo, by 1, 2 likes (2, 3) """
        self.rating4 = Rating.objects.create(
            user=self.user1, recipe=self.recipe1, stars=5, 
            content="Excellent recipe, a hit with the family.", 
            photo=media_utils.generate_test_image(),
            created_at=utc_now() - timedelta(days=8)
        )
        self.rating4.liked_by.add(self.user2, self.user3)

        """ Rating 5: 4 stars, content with 'great', has photo, by 1, 3 likes (2, 3, 4) """
        self.rating5 = Rating.objects.create(
            user=self.user1, recipe=self.recipe2, stars=4, 
            content="Great smoothie, very refreshing!", 
            photo=media_utils.generate_test_image(),
            created_at=utc_now() - timedelta(days=3)
        )
        self.rating5.liked_by.add(self.user2, self.user3, self.user4)

        """ Rating 6: 2 stars, content with 'decent', no photo, by 3, 0 likes """
        self.rating6 = Rating.objects.create(
            user=self.user3, recipe=self.recipe2, stars=2, 
            content="Decent taste, but not my favorite.", 
            created_at=utc_now() - timedelta(days=5)
        )

        """ Rating 7: 3 stars, no content, no photo, by 2, 2 likes (1, 4) """
        self.rating7 = Rating.objects.create(
            user=self.user2, recipe=self.recipe2, stars=3,
            created_at=utc_now() - timedelta(days=7)
        )
        self.rating7.liked_by.add(self.user1, self.user4)

        """ Rating 8: 4 stars, content with 'great', has photo, by 4, 3 likes (1, 2, 3) """
        self.rating8 = Rating.objects.create(
            user=self.user4, recipe=self.recipe2, stars=4, 
            content="Great smoothie, very healthy!", 
            photo=media_utils.generate_test_image(),
            created_at=utc_now() - timedelta(days=9)
        )
        self.rating8.liked_by.add(self.user1, self.user2, self.user3)


    def tearDown(self):
        media_utils.delete_test_media()


    def test_recipe_data_filter(self):
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.user_token}"}
        params = {
            'user': self.user2.pk,
            'has_content': True,
            'page': 1, 'page_size': 2
        }
        response: Response = self.client.get(f'/rating/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['count'], 1)
        expected_result = {
            'id': self.rating1.pk, 'photo': self.rating1.photo.url, 
            'stars': 5, 'content': self.rating1.content, 
            'created_at': self.rating1.created_at.isoformat(), 
            'edited_at': None, 'like_count': 4, 'liked': True,
            'recipe': {
                'id': 1, 'photo': None, 'user': {
                    'id': self.rating1.recipe.user.pk, 'photo': None, 'name': 'User One', 
                    'created_at': self.rating1.recipe.user.created_at.isoformat()
                }, 
                'name': 'Pancakes', 'title': 'Fluffy Pancakes',
                'prep_time': 20, 'calories': 300, 
                'created_at': self.rating1.recipe.created_at.isoformat()
            }
        }
        self.assertEqual(response.data['results'][0], expected_result)

    
    def test_user_data_filter(self):
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.user_token}"}
        params = {
            'recipe': self.recipe1.pk,
            'liked': True,
            'order_by': ['created_at', '-like_count', '-stars'],
            'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/rating/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], self.rating3.pk)
        self.assertEqual(response.data['results'][1]['id'], self.rating1.pk)
        self.assertNotIn('recipe', response.data['results'][0])
        self.assertNotIn('recipe', response.data['results'][1])
        self.assertEqual(response.data['results'][0]['user']['id'], self.user4.pk)
        expected_user = {
            'id': self.user2.pk, 'photo': None, 'name': 'User Two', 
            'created_at': self.user2.created_at.isoformat()
        }
        self.assertEqual(response.data['results'][1]['user'], expected_user)


    def test_both_data_filter(self):
        headers = {}
        params = {
            'liked': True,
            'search_string': "great",
            'order_by': ['-like_count', '-stars', '-created_at'],
            'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/rating/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['id'], self.rating1.pk)
        self.assertEqual(response.data['results'][1]['id'], self.rating5.pk)
        self.assertEqual(response.data['results'][2]['id'], self.rating8.pk)
        self.assertIsNone(response.data['results'][0]['liked'])
        self.assertIn('user', response.data['results'][0])
        self.assertIn('recipe', response.data['results'][0])



@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestRecipeFilter(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create(email=f"test_user@example.com", name=f"Test User")
        self.user_token = security.generate_token(self.test_user)
        self.moderator_user = User.objects.create(email=f"moderator@example.com", name=f"Moderator User", moderator=True)
        self.moderator_token = security.generate_token(self.moderator_user)
        """ 6 Categories """
        self.category1 = Category.objects.create(name=f"Category 1", photo=media_utils.generate_test_image())
        self.category2 = Category.objects.create(name=f"Category 2", photo=media_utils.generate_test_image())
        self.category3 = Category.objects.create(name=f"Category 3", photo=media_utils.generate_test_image())
        self.category4 = Category.objects.create(name=f"Category 4", photo=media_utils.generate_test_image())
        self.category5 = Category.objects.create(name=f"Category 5", photo=media_utils.generate_test_image())
        self.category6 = Category.objects.create(name=f"Category 6", photo=media_utils.generate_test_image())
        """ Favoured categories """
        self.category1.favoured_by.add(self.test_user)
        self.category3.favoured_by.add(self.test_user)
        self.category6.favoured_by.add(self.test_user)
        """ 6 Ingredients """
        self.ingredient1 = Ingredient.objects.create(
            name=f"Ingredient 1", unit="g", photo=media_utils.generate_test_image()
        )
        self.ingredient2 = Ingredient.objects.create(
            name=f"Ingredient 2", unit="kg", photo=media_utils.generate_test_image()
        )
        self.ingredient3 = Ingredient.objects.create(
            name=f"Ingredient 3", unit="mg", photo=media_utils.generate_test_image()
        )
        self.ingredient4 = Ingredient.objects.create(
            name=f"Ingredient 4", unit="mu", photo=media_utils.generate_test_image()
        )
        self.ingredient5 = Ingredient.objects.create(
            name=f"Ingredient 5", unit="kg", photo=media_utils.generate_test_image()
        )
        self.ingredient6 = Ingredient.objects.create(
            name=f"Ingredient 6", unit="g", photo=media_utils.generate_test_image()
        )
        """ Inventory ingredients """
        UserIngredient.objects.create(user=self.test_user, ingredient=self.ingredient1, amount=300)
        UserIngredient.objects.create(user=self.test_user, ingredient=self.ingredient2, amount=250)
        UserIngredient.objects.create(user=self.test_user, ingredient=self.ingredient3, amount=400)
        UserIngredient.objects.create(user=self.test_user, ingredient=self.ingredient4, amount=175)
        UserIngredient.objects.create(user=self.test_user, ingredient=self.ingredient5, amount=250)
        """ 3 Extra users """
        self.user1 = User.objects.create(email=f"user1@example.com", name=f"User 1")
        self.user2 = User.objects.create(email=f"user2@example.com", name=f"User 2")
        self.user3 = User.objects.create(email=f"user3@example.com", name=f"User 3")

        """ Recipe 1 (Great) by test_user: 2 ratings (1 new) 4.5 (4.0 new), 
            3 categories (1, 2, 3), 2 ingredients (1, 4), favoured, photo (2), 6 servings """
        self.recipe1 = Recipe.objects.create(
            user=self.test_user, name="Recipe 1", title="Great Recipe 1",
            submit_status=SubmitStatuses.ACCEPTED, 
            prep_time=110, calories=290,
            created_at=utc_now() - timedelta(days=2)
        )
        self.recipe1.favoured_by.add(self.test_user)
        self.recipe1.categories.add(self.category1, self.category2, self.category3)
        RecipePhoto.objects.create(recipe=self.recipe1, photo=media_utils.generate_test_image(), number=1)
        RecipePhoto.objects.create(recipe=self.recipe1, photo=media_utils.generate_test_image(), number=2)
        RecipeIngredient.objects.create(recipe=self.recipe1, ingredient=self.ingredient1, amount=50)
        RecipeIngredient.objects.create(recipe=self.recipe1, ingredient=self.ingredient4, amount=20)
        Rating.objects.create(user=self.user2, recipe=self.recipe1, stars=4)
        Rating.objects.create(user=self.user3, recipe=self.recipe1, stars=5, created_at=utc_now() - timedelta(days=10))

        """ Recipe 2 (Delicious) by test_user: 0 ratings, 
            3 categories (2, 6), 2 ingredients (5, 2), DENIED """
        self.recipe2 = Recipe.objects.create(
            user=self.test_user, name="Recipe 2", title="Delicious Recipe 2", 
            submit_status=SubmitStatuses.DENIED, deny_message = "This Recipe is denied",
            prep_time=30, calories=250,
            created_at=utc_now() - timedelta(days=1)
        )
        self.recipe2.categories.add(self.category2, self.category6)
        RecipeIngredient.objects.create(recipe=self.recipe2, ingredient=self.ingredient5, amount=200)
        RecipeIngredient.objects.create(recipe=self.recipe2, ingredient=self.ingredient2, amount=100)

        """ Recipe 3 (Great) by user1: 3 ratings (0 new) 3.0, 
            1 categories (4), 2 ingredients (1, 4), favoured, 3 servings"""
        self.recipe3 = Recipe.objects.create(
            user=self.user1, name="Recipe 3", title="Great Recipe 3", 
            submit_status=SubmitStatuses.ACCEPTED, 
            prep_time=60, calories=400,
            created_at=utc_now() - timedelta(days=10)
        )
        self.recipe3.categories.add(self.category4)
        RecipeIngredient.objects.create(recipe=self.recipe3, ingredient=self.ingredient1, amount=100)
        RecipeIngredient.objects.create(recipe=self.recipe3, ingredient=self.ingredient4, amount=50)
        Rating.objects.create(user=self.user1, recipe=self.recipe3, stars=3, created_at=utc_now() - timedelta(days=10))
        Rating.objects.create(user=self.user3, recipe=self.recipe3, stars=2, created_at=utc_now() - timedelta(days=9))
        Rating.objects.create(user=self.user2, recipe=self.recipe3, stars=4, created_at=utc_now() - timedelta(days=8))
        self.recipe3.favoured_by.add(self.test_user)

        """ Recipe 4 (Delicious) by user1: 1 ratings (1 new) 1.0, 
            1 categories (1, 6), 3 ingredients (1, 2, 5), 3 servings """
        self.recipe4 = Recipe.objects.create(
            user=self.user1, name="Recipe 4", title="Delicious Recipe 4", 
            submit_status=SubmitStatuses.ACCEPTED, 
            prep_time=20, calories=200,
            created_at=utc_now() - timedelta(days=2)
        )
        self.recipe4.categories.add(self.category1, self.category6)
        RecipeIngredient.objects.create(recipe=self.recipe4, ingredient=self.ingredient1, amount=50)
        RecipeIngredient.objects.create(recipe=self.recipe4, ingredient=self.ingredient2, amount=70)
        RecipeIngredient.objects.create(recipe=self.recipe4, ingredient=self.ingredient5, amount=10)
        Rating.objects.create(user=self.user1, recipe=self.recipe4, stars=1)

        """ Recipe 5 (Great) by user2: 0 ratings, 
            1 categories (1), 1 ingredients (6), favoured, 0 servings """
        self.recipe5 = Recipe.objects.create(
            user=self.user2, name="Recipe 5", title="Great Recipe 5", 
            submit_status=SubmitStatuses.ACCEPTED, 
            prep_time=50, calories=350,
            created_at=utc_now() - timedelta(days=5)
        )
        self.recipe5.categories.add(self.category1)
        RecipeIngredient.objects.create(recipe=self.recipe5, ingredient=self.ingredient6, amount=70)
        self.recipe5.favoured_by.add(self.test_user)

        """ Recipe 6 (Great) by user3: 4 ratings (4 new) 2.5 (2.5 new),
            2 categories (1, 3), 2 ingredients (3, 4), 1 servings """
        self.recipe6 = Recipe.objects.create(
            user=self.user3, name="Recipe 6", title="Great Recipe 6", 
            submit_status=SubmitStatuses.ACCEPTED, 
            prep_time=40, calories=280,
            created_at=utc_now() - timedelta(days=7)
        )
        self.recipe6.categories.add(self.category1, self.category3)
        RecipeIngredient.objects.create(recipe=self.recipe6, ingredient=self.ingredient3, amount=50)
        RecipeIngredient.objects.create(recipe=self.recipe6, ingredient=self.ingredient4, amount=115)
        Rating.objects.create(user=self.user1, recipe=self.recipe6, stars=2)
        Rating.objects.create(user=self.user2, recipe=self.recipe6, stars=4)
        Rating.objects.create(user=self.user3, recipe=self.recipe6, stars=1)
        Rating.objects.create(user=self.test_user, recipe=self.recipe6, stars=3)

        """ Recipe 7 (Delicious) by user3: 0 ratings,
            2 categories (5), 2 ingredients (1, 2), SUBMITTED """
        self.recipe7 = Recipe.objects.create(
            user=self.user3, name="Recipe 7", title="Delicious Recipe 7", 
            submit_status=SubmitStatuses.SUBMITTED,
            prep_time=40, calories=280,
            created_at=utc_now() - timedelta(days=17)
        )
        self.recipe7.categories.add(self.category5)
        RecipeIngredient.objects.create(recipe=self.recipe7, ingredient=self.ingredient1, amount=115)
        RecipeIngredient.objects.create(recipe=self.recipe7, ingredient=self.ingredient2, amount=200)


    def tearDown(self):
        media_utils.delete_test_media()


    def test_data(self):
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.user_token}"}
        params = {
            'user': self.test_user.pk, 'favourite_category': True,
            'submit_status': SubmitStatuses.ACCEPTED, 
            'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        expected_recipe = {
            'id': self.recipe1.pk, 'name': 'Recipe 1', 'title': 'Great Recipe 1',
            'photo': RecipePhoto.objects.filter(recipe=self.recipe1, number=1).first().photo.url,
            'created_at': self.recipe1.created_at.isoformat(),
            'deny_message': None, 'favoured': True,
            'prep_time': 110, 'calories': 290,
            'rating_count': 2, 'avg_rating': 4.5,
            'submit_status': 'ACCEPTED',
            'user': {
                'created_at': self.test_user.created_at.isoformat(),
                'id': self.test_user.pk, 
                'name': 'Test User', 'photo': None
                }
            }
        self.assertEqual(response.data['results'][0], expected_recipe)


    def test_submit_status(self):
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.user_token}"}
        params = {'submit_status': SubmitStatuses.DENIED, 'page': 1, 'page_size': 5}
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], {'submit_status': ['invalid submit_status value.']})
        params['user'] = self.test_user.pk
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.recipe2.pk)
        self.assertEqual(response.data['results'][0]['deny_message'], "This Recipe is denied")
        headers = {}
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], {'submit_status': ['invalid submit_status value.']})
        params['user'] = self.user3.pk
        params['submit_status'] = SubmitStatuses.SUBMITTED
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], {'submit_status': ['invalid submit_status value.']})        
        params.pop('user')
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.moderator_token}"}
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.recipe7.pk)  
        params['submit_status'] = SubmitStatuses.DENIED
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], {'submit_status': ['invalid submit_status value.']})


    def test_categories(self):
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.user_token}"}
        params = {
            'favourite_category': True,
            'prep_time_limit': 100, 
            'calories_limit': 600, 'servings': 2,
            'order_by': ['-created_at', '-name'],
            'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], self.recipe4.pk)
        self.assertEqual(response.data['results'][1]['id'], self.recipe6.pk)
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.user_token}"}
        params = {
            'categories': [self.category2.pk, self.category3.pk],
            'order_by': ['created_at', 'name'],
            'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], self.recipe6.pk)
        self.assertEqual(response.data['results'][1]['id'], self.recipe1.pk)


    def test_sufficient_ingrediens(self):
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.user_token}"}
        params = {
            'favoured': True, 'sufficient_ingrediens': True, 
            'servings': 3, 'order_by': ['name'],
            'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], self.recipe1.pk)
        self.assertEqual(response.data['results'][1]['id'], self.recipe3.pk)
        params['servings'] = 6
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.recipe1.pk)
        params['servings'] = 7
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)


    def test_ordering(self):
        params = {
            'order_by': ['-rating_count', '-created_at', 'name'],
            'order_time_window': 5, 'search_string': "great's", 
            'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(response.data['results'][0]['id'], self.recipe6.pk)
        self.assertEqual(response.data['results'][0]['rating_count'], 4)
        self.assertEqual(response.data['results'][1]['id'], self.recipe1.pk)
        self.assertEqual(response.data['results'][1]['rating_count'], 2)
        self.assertEqual(response.data['results'][2]['id'], self.recipe5.pk)
        self.assertEqual(response.data['results'][2]['rating_count'], 0)
        self.assertEqual(response.data['results'][3]['id'], self.recipe3.pk)
        self.assertEqual(response.data['results'][3]['rating_count'], 3)
        params = {
            'order_by': ['-avg_rating', '-created_at', 'name'],
            'order_time_window': 5, 'page': 1, 'page_size': 5
        }
        response: Response = self.client.get(f'/recipe/filter/paged', params, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        self.assertEqual(response.data['results'][0]['id'], self.recipe1.pk)
        self.assertEqual(response.data['results'][0]['avg_rating'], 4.5)
        self.assertEqual(response.data['results'][1]['id'], self.recipe6.pk)
        self.assertEqual(response.data['results'][1]['avg_rating'], 2.5)
        self.assertEqual(response.data['results'][2]['id'], self.recipe4.pk)
        self.assertEqual(response.data['results'][2]['avg_rating'], 1.0)
        self.assertEqual(response.data['results'][3]['id'], self.recipe5.pk)
        self.assertEqual(response.data['results'][3]['avg_rating'], None)
        self.assertEqual(response.data['results'][4]['id'], self.recipe3.pk)
        self.assertEqual(response.data['results'][4]['avg_rating'], 3.0)
