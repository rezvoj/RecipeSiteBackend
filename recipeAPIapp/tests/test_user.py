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


class TestReport(APITestCase):
    def setUp(self):
        self.reporting_user = User.objects.create(email="reporting_user@example.com", name="Reporting User")
        self.reporting_token = security.generate_token(self.reporting_user)
        self.reported_user = User.objects.create(email="reported_user@example.com", name="Reported User")
        self.banned_user = User.objects.create(email="banned_user@example.com", name="Banned User", banned=True)

    def test_successful_report(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.reporting_token}'}
        response: Response = self.client.post(f'/user/report/{self.reported_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserReport.objects.filter(user=self.reporting_user, reported=self.reported_user).exists())

    def test_duplicate_report(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.reporting_token}'}
        response: Response = self.client.post(f'/user/report/{self.reported_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response: Response = self.client.post(f'/user/report/{self.reported_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        expected_data = {'detail': {'non_field_errors': ['user already reported.']}}
        self.assertEqual(response.data, expected_data)

    def test_report_creation_limit_exceeded(self):
        for i in range(Config.ContentLimits.report[0]):
            new_reported_user = User.objects.create(email=f"reported_user_{i}@example.com", name=f"Reported User {i}")
            UserReport.objects.create(user=self.reporting_user, reported=new_reported_user)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.reporting_token}'}
        new_reported_user = User.objects.create(email="another_user@example.com", name="Another User")
        response: Response = self.client.post(f'/user/report/{new_reported_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'limit': 15, 'hours': 24}}
        self.assertEqual(response.data, expected_data)

    def test_report_banned_user(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.reporting_token}'}
        response: Response = self.client.post(f'/user/report/{self.banned_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestUserBan(APITestCase):
    def setUp(self):
        self.moderator_user = User.objects.create(email="moderator_user@example.com", name="Moderator User", moderator=True)
        self.moderator_token = security.generate_token(self.moderator_user)
        self.another_moderator = User.objects.create(email="moderator2@example.com", name="Another Moderator", moderator=True)
        self.regular_user = User.objects.create(email="regular_user@example.com", name="Regular User")
        self.recipe = Recipe.objects.create(user=self.regular_user, name="Recipe", title="Title", prep_time=10, calories=10)
    
    def test_successful_ban_by_admin(self):
        headers = {'HTTP_ADMINCODE': 'TEST_ADMIN_CODE'}
        response: Response = self.client.post(f'/user/ban/{self.regular_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(pk=self.regular_user.pk).exists())
        banned_user = User.objects.filter(email="regular_user@example.com", banned=True).first()
        self.assertIsNotNone(banned_user)
        self.assertNotEqual(banned_user.pk, self.regular_user.pk)
        self.assertFalse(Recipe.objects.filter(user=banned_user).exists())

    def test_successful_ban_by_moderator(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.post(f'/user/ban/{self.regular_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(pk=self.regular_user.pk).exists())
        banned_user = User.objects.filter(email="regular_user@example.com", banned=True).first()
        self.assertIsNotNone(banned_user)
        self.assertNotEqual(banned_user.pk, self.regular_user.pk)
        self.assertFalse(Recipe.objects.filter(user=banned_user).exists())

    def test_attempt_ban_moderator_by_another_moderator(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.post(f'/user/ban/{self.another_moderator.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_successful_ban_moderator_by_admin(self):
        headers = {'HTTP_ADMINCODE': 'TEST_ADMIN_CODE'}
        response: Response = self.client.post(f'/user/ban/{self.another_moderator.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(pk=self.another_moderator.pk).exists())
        banned_user = User.objects.filter(email="moderator2@example.com", banned=True).first()
        self.assertIsNotNone(banned_user)
        self.assertNotEqual(banned_user.pk, self.another_moderator.pk)
        self.assertFalse(banned_user.moderator)

    def test_attempt_ban_already_banned_user(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.post(f'/user/ban/{self.regular_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response: Response = self.client.post(f'/user/ban/{self.regular_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestDismissReports(APITestCase):
    def setUp(self):
        self.moderator_user = User.objects.create(email="moderator_user@example.com", name="Moderator User", moderator=True)
        self.moderator_token = security.generate_token(self.moderator_user)
        self.regular_user = User.objects.create(email="regular_user@example.com", name="Regular User")
        self.another_moderator = User.objects.create(email="moderator2@example.com", name="Another Moderator", moderator=True)
        self.banned_user = User.objects.create(email="banned_user@example.com", name="Banned User", banned=True)
        self.report1 = UserReport.objects.create(user=self.moderator_user, reported=self.another_moderator)
        self.report2 = UserReport.objects.create(user=self.another_moderator, reported=self.regular_user)

    def test_successful_dismiss_reports_by_admin(self):
        headers = {'HTTP_ADMINCODE': 'TEST_ADMIN_CODE'}
        response: Response = self.client.delete(f'/user/dismiss-reports/{self.regular_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserReport.objects.filter(reported=self.regular_user).exists())

    def test_successful_dismiss_reports_by_moderator(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/user/dismiss-reports/{self.regular_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserReport.objects.filter(reported=self.regular_user).exists())

    def test_attempt_dismiss_reports_for_moderator_by_another_moderator(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/user/dismiss-reports/{self.another_moderator.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(UserReport.objects.filter(reported=self.another_moderator).exists())

    def test_successful_dismiss_reports_for_moderator_by_admin(self):
        UserReport.objects.create(user=self.regular_user, reported=self.another_moderator)
        headers = {'HTTP_ADMINCODE': 'TEST_ADMIN_CODE'}
        response: Response = self.client.delete(f'/user/dismiss-reports/{self.another_moderator.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserReport.objects.filter(reported=self.another_moderator).exists())

    def test_attempt_dismiss_reports_for_banned_user(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.moderator_token}'}
        response: Response = self.client.delete(f'/user/dismiss-reports/{self.banned_user.pk}', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
