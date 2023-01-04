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
