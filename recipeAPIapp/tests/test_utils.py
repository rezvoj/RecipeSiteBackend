import logging
from django.urls import path
from django.http import Http404
from django.test import override_settings
from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.test import APITestCase
import recipeAPIapp.utils.exception as Exceptions



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
