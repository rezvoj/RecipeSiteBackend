from datetime import timedelta
from django.test import override_settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
import recipeAPIapp.utils.security as security
from recipeAPIapp.apps import Config
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.models.user import User, EmailRecord



class TestToken(APITestCase):
    def setUp(self):
        self.user = User(email="test@example.com", name="Test User")
        security.set_password(self.user, "testpassword")
        self.user.save()
        self.old_token = security.generate_token(self.user)

    def test_valid_token(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.old_token}'}
        response: Response = self.client.post('/auth/token', **headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        headers = {'HTTP_AUTHORIZATION': f"Bearer {response.data['token']}"}
        response: Response = self.client.post('/auth/token', **headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer invalidtoken'}
        response: Response = self.client.post('/auth/token', **headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('token', response.data)


class TestLogin(APITestCase):    
    def setUp(self):
        self.user = User(email="test@example.com", name="Test User")
        security.set_password(self.user, "testpassword")
        self.user.save()

    def test_valid_credentials(self):
        response: Response = self.client.post(
            '/auth/login', data={
                "email": "test@example.com",
                "password": "testpassword"
            }, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_invalid_email(self):
        response: Response = self.client.post(
            '/auth/login', data={
                "email": "wrongemail@example.com",
                "password": "testpassword"
            }, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'non_field_errors': ['invalid email or password.']}}
        self.assertEqual(response.data, expected_data)

    def test_login_invalid_password(self):
        response: Response = self.client.post(
            '/auth/login', data={
                "email": "test@example.com",
                "password": "wrongpassword"
            }, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'non_field_errors': ['invalid email or password.']}}
        self.assertEqual(response.data, expected_data)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TestUpdate(APITestCase):    
    def setUp(self):
        self.user = User(email="test@example.com", name="Test User")
        security.set_password(self.user, "testpassword")
        self.user.save()
        self.token = security.generate_token(self.user)
    
    def test_update_email(self):
        new_email = "newemail@example.com"
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.put(
            '/auth/update', data={
                "password": "testpassword",
                "email": new_email
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        previous_di = self.user.details_iteration
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, new_email)
        self.assertEqual(self.user.details_iteration, previous_di + 1)
    
    def test_update_password(self):
        new_password = "new$assword"
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.put(
            '/auth/update', data={
                "password": "testpassword",
                "new_password": new_password
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        previous_di = self.user.details_iteration
        self.user.refresh_from_db()
        self.assertTrue(security.check_password(self.user, new_password))
        self.assertEqual(self.user.details_iteration, previous_di + 1)

    def test_update_password_and_email(self):
        new_email = "newemail@example.com"
        new_password = "new$assword"
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.put(
            '/auth/update', data={
                "password": "testpassword",
                "email": new_email,
                "new_password": new_password
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        previous_di = self.user.details_iteration
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, new_email)
        self.assertTrue(security.check_password(self.user, new_password))
        self.assertEqual(self.user.details_iteration, previous_di + 1)

    def test_invalid_password(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.put(
            '/auth/update', data={
                "password": "wrongpassword",
                "email": "newemail@example.com"
            }, format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        previous_di = self.user.details_iteration
        previous_email = self.user.email
        self.user.refresh_from_db()
        expected_data = {'detail': {'password': ['invalid password.']}}
        self.assertEqual(response.data, expected_data)
        self.assertEqual(self.user.email, previous_email)
        self.assertEqual(self.user.details_iteration, previous_di)

    def test_nothing_to_change(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.put(
            '/auth/update', 
            data={"password": "testpassword"}, 
            format='json', **headers
        )
        previous_di = self.user.details_iteration
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'non_field_errors': ['nothing to change.']}}
        self.assertEqual(response.data, expected_data)
        self.assertEqual(self.user.details_iteration, previous_di)
