import logging, jwt
from datetime import timedelta
from django.urls import path
from django.http import Http404
from django.test import override_settings
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.test import APITestCase, APIRequestFactory
import recipeAPIapp.utils.exception as Exceptions
import recipeAPIapp.utils.security as Security
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.models.user import User



class ExceptionView(APIView):
    def get(self, _, exception_type):
        match exception_type:
            case 'verification-error':
                raise Exceptions.VerificationException({
                    "name": ["has to be longer than 3 characters."],
                    "non_field_errors": ["invalid email or password."]
                })
            case 'content-limit-error':
                raise Exceptions.ContentLimitException({
                    "limit": 10, 
                    "hours": 1
                })
            case 'permission-denied':
                raise PermissionDenied()
            case 'banned':
                raise Exceptions.BannedException()
            case 'not-found':
                raise Http404()
            case _:
                raise Exception("An internal error occurred.")


urlpatterns = [
    path('test/exceptions/<str:exception_type>', ExceptionView.as_view()),
]


@override_settings(ROOT_URLCONF='recipeAPIapp.tests.test_utils')
class TestExceptionHandler(APITestCase):
    def setUp(self):
        self.log = logging.getLogger('recipeAPIapp.utils.exception')
        self.original_log_level = self.log.level
        self.log.setLevel(logging.CRITICAL)

    def tearDown(self):
        self.log.setLevel(self.original_log_level)

    def test_verification_exception(self):
        response: Response = self.client.get('/test/exceptions/verification-error')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], {
            "name": ["has to be longer than 3 characters."],
            "non_field_errors": ["invalid email or password."]
        })

    def test_content_limit_exception(self):
        response: Response = self.client.get('/test/exceptions/content-limit-error')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], {"limit": 10, "hours": 1})

    def test_permission_denied_exception(self):
        response: Response = self.client.get('/test/exceptions/permission-denied')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {})

    def test_banned_exception(self):
        response: Response = self.client.get('/test/exceptions/banned')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You have been banned.')

    def test_http_404_exception(self):
        response: Response = self.client.get('/test/exceptions/not-found')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {})

    def test_internal_server_error(self):
        response: Response = self.client.get('/test/exceptions/internal-server-error')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {})


class TestSecurity(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        salt = PBKDF2PasswordHasher().salt()
        self.user = User.objects.create(
            email='test@example.com', name='Test User',
            password_hash=PBKDF2PasswordHasher().encode('password123', salt),
            details_iteration=1
        )

    def test_generate_token(self):
        token = Security.generate_token(self.user, issue_for_days=7)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        self.assertEqual(payload['id'], self.user.pk)
        self.assertEqual(payload['di'], self.user.details_iteration)
        self.assertTrue('exp' in payload)
        self.assertGreater(payload['exp'], utc_now().timestamp())

    def test_check_password(self):
        self.assertTrue(Security.check_password(self.user, 'password123'))
        self.assertFalse(Security.check_password(self.user, 'wrongpassword'))

    def test_set_password(self):
        Security.set_password(self.user, 'newpassword')
        self.assertTrue(Security.check_password(self.user, 'newpassword'))
        self.assertFalse(Security.check_password(self.user, 'password123'))

    def test_authenticate_valid_token(self):
        token = Security.generate_token(self.user, issue_for_days=7)
        request = self.factory.get('', HTTP_AUTHORIZATION=f'Bearer {token}')
        user, _ = Security.Authentication().authenticate(request)
        self.assertEqual(user, self.user)

    def test_authenticate_invalid_token(self):
        request = self.factory.get('', HTTP_AUTHORIZATION='Bearer invalidtoken')
        user, _ = Security.Authentication().authenticate(request)
        self.assertIsNone(user)

    def test_authenticate_missing_token(self):
        request = self.factory.get('')
        user, _ = Security.Authentication().authenticate(request)
        self.assertIsNone(user)

    def test_authenticate_banned_user(self):
        self.user.banned = True
        self.user.save()
        token = Security.generate_token(self.user, issue_for_days=7)
        request = self.factory.get('', HTTP_AUTHORIZATION=f'Bearer {token}')
        with self.assertRaises(Exceptions.BannedException):
            Security.Authentication().authenticate(request)

    def test_authenticate_user_details_changed(self):
        token = jwt.encode({
            'id': self.user.pk,
            'di': self.user.details_iteration + 1,
            'exp': utc_now() + timedelta(days=7)
        }, settings.SECRET_KEY, algorithm='HS256')
        request = self.factory.get('', HTTP_AUTHORIZATION=f'Bearer {token}')
        user, _ = Security.Authentication().authenticate(request)
        self.assertIsNone(user)
