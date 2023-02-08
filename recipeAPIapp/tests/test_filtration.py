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
