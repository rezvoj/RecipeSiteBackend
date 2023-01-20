from django.test import override_settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
import recipeAPIapp.utils.security as security
import recipeAPIapp.tests.media_utils as media_utils
from recipeAPIapp.apps import Config
from recipeAPIapp.models.user import User, UserReport
from recipeAPIapp.models.recipe import Recipe, Rating, SubmitStatuses



@override_settings(DEFAULT_FILE_STORAGE=media_utils.TEST_DEFAULT_FILE_STORAGE)
@override_settings(MEDIA_ROOT=media_utils.TEST_MEDIA_ROOT)
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TestUserCUD(APITestCase):
    def setUp(self):
        self.user = User(email="test@example.com", name="Test User")
        security.set_password(self.user, "testpassword")
        self.user.save()
        self.token = security.generate_token(self.user)

    def tearDown(self):
        media_utils.delete_test_media()

    def test_create_user(self):
        photo = media_utils.generate_test_image()
        response: Response = self.client.post(
            '/user', data={
                "photo": photo,
                "email": "newuser@example.com",
                "name": "New User",
                "about": "About New User",
                "password": "newuserpassword"
            }, format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        new_user = User.objects.get(email="newuser@example.com")
        self.assertEqual(new_user.name, "New User")
        self.assertEqual(new_user.about, "About New User")
        self.assertTrue(security.check_password(new_user, "newuserpassword"))
        self.assertIsNotNone(new_user.vcode)
        self.assertIsNotNone(new_user.vcode_expiry)

    def test_update_user(self):
        photo = media_utils.generate_test_image()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.put(
            '/user', data={
                "photo": photo,
                "name": "Updated Name",
                "about": "Updated About"
            }, 
            format='multipart', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated Name")
        self.assertEqual(self.user.about, "Updated About")

    def test_delete_user(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.delete('/user', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(email="test@example.com").exists())

    def test_update_user_unauthenticated(self):
        response: Response = self.client.put(
            '/user', data={
                "name": "Updated Name",
                "about": "Updated About"
            }, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.name, "Updated Name")
        self.assertNotEqual(self.user.about, "Updated About")

    def test_delete_user_unauthenticated(self):
        response: Response = self.client.delete('/user', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(User.objects.filter(email="test@example.com").exists())


@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestModeratorChange(APITestCase):
    def setUp(self):
        self.regular_user = User(email="user@example.com", name="Regular User")
        security.set_password(self.regular_user, "userpassword")
        self.regular_user.save()
        self.banned_user = User(email="banned@example.com", name="Banned User", banned=True)
        security.set_password(self.banned_user, "bannedpassword")
        self.banned_user.save()

    def test_change_moderator_status(self):
        headers = {'HTTP_ADMINCODE': 'TEST_ADMIN_CODE'}
        response: Response = self.client.put(
            f'/user/change-moderator/{self.regular_user.pk}', 
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.moderator)
        response: Response = self.client.put(
            f'/user/change-moderator/{self.regular_user.pk}', 
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.moderator)

    def test_change_moderator_status_non_admin(self):
        headers = {'HTTP_ADMINCODE': 'wrong_code'}
        response: Response = self.client.put(
            f'/user/change-moderator/{self.regular_user.pk}', 
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_moderator_status_banned_user(self):
        headers = {'HTTP_ADMINCODE': 'TEST_ADMIN_CODE'}
        response: Response = self.client.put(
            f'/user/change-moderator/{self.banned_user.pk}', 
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
