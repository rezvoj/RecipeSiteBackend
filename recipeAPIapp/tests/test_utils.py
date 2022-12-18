import logging, jwt, io
import django.core.mail as mail
import django.utils.crypto as django_crypto
from datetime import timedelta
from PIL import Image
from django.urls import path
from django.http import Http404
from django.test import override_settings
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.test import APITestCase, APIRequestFactory
import recipeAPIapp.utils.exception as Exceptions
import recipeAPIapp.utils.permission as Permissions
import recipeAPIapp.utils.security as Security
import recipeAPIapp.utils.validation as Validation
import recipeAPIapp.utils.verification as Verification
from recipeAPIapp.apps import Config
from recipeAPIapp.utils.exception import VerificationException
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.models.user import User, EmailRecord
from recipeAPIapp.models.recipe import Recipe



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


@override_settings(APP_ADMIN_CODE='TEST_ADMIN_CODE')
class TestPermissions(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin_code = 'correct_admin_code'
        self.unverified_user = User.objects.create(
            email='unverified@example.com', name='Unverified User',
            vcode='1234', moderator=False
        )
        self.user = User.objects.create(
            email='verified@example.com', name='Verified User',
            vcode=None, moderator=False
        )
        self.moderator_user = User.objects.create(
            email='moderator@example.com', name='Moderator User',
            moderator=True
        )

    def test_user_function(self):
        request = self.factory.get('')
        request.user = self.user
        result = Permissions.user(request)
        self.assertEqual(result, self.user)
        request.user = None
        with self.assertRaises(PermissionDenied):
            Permissions.user(request)

    def test_verified_function(self):
        request = self.factory.get('')
        request.user = self.user
        result = Permissions.verified(request)
        self.assertEqual(result, self.user)
        request.user = self.unverified_user
        with self.assertRaises(PermissionDenied):
            Permissions.verified(request)

    def test_is_admin_function(self):
        request = self.factory.get('')
        result = Permissions.is_admin(request)
        self.assertFalse(result)
        request.META['HTTP_ADMINCODE'] = 'wrong_code'
        result = Permissions.is_admin(request)
        self.assertFalse(result)
        request.META['HTTP_ADMINCODE'] = 'TEST_ADMIN_CODE'
        result = Permissions.is_admin(request)
        self.assertTrue(result)

    def test_admin_function(self):
        request = self.factory.get('')
        request.user = User()
        request.META['HTTP_ADMINCODE'] = 'TEST_ADMIN_CODE'
        result = Permissions.admin(request)
        self.assertEqual(result, request.user)
        request.META['HTTP_ADMINCODE'] = 'wrong_code'
        with self.assertRaises(PermissionDenied):
            Permissions.admin(request)
        request.META.pop('HTTP_ADMINCODE')
        with self.assertRaises(PermissionDenied):
            Permissions.admin(request)

    def test_is_admin_or_moderator_function(self):
        request = self.factory.get('')
        request.user = self.moderator_user
        result = Permissions.is_admin_or_moderator(request)
        self.assertTrue(result)
        request = self.factory.get('')
        request.user = self.user
        result = Permissions.is_admin_or_moderator(request)
        self.assertFalse(result)
        request.META['HTTP_ADMINCODE'] = 'TEST_ADMIN_CODE'
        result = Permissions.is_admin_or_moderator(request)
        self.assertTrue(result)

    def test_admin_or_moderator_function(self):
        request = self.factory.get('')
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            Permissions.admin_or_moderator(request)
        request.META['HTTP_ADMINCODE'] = 'TEST_ADMIN_CODE'
        result = Permissions.admin_or_moderator(request)
        self.assertEqual(result, self.user)
        request.user = self.moderator_user
        result = Permissions.admin_or_moderator(request)
        self.assertEqual(result, self.moderator_user)

    def test_user_id_function(self):
        request = self.factory.get('')
        request.user = None
        result = Permissions.user_id(request)
        self.assertEqual(result, 'anon')
        request.user = self.user
        result = Permissions.user_id(request)
        self.assertEqual(result, self.user.pk)
        request.META['HTTP_ADMINCODE'] = 'TEST_ADMIN_CODE'
        result = Permissions.user_id(request)
        self.assertEqual(result, 'admin')


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


class TestValidation(APITestCase):
    class DummySerializer(serializers.Serializer):
        name = serializers.CharField(max_length=100)
        age = serializers.IntegerField()
        def validate(self, data):
            if data['name'] == 'Invalid Name':
                raise serializers.ValidationError("Invalid Name")
            return data

    def setUp(self):
        self.user = User.objects.create(email='test@abc.com', name='Test User')

    def test_photo_with_valid_image(self):
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='black')
        image.save(file, format="JPEG")
        file.seek(0)
        photo = SimpleUploadedFile('test_image.jpg', file.read(), content_type='image/jpeg')
        result = Validation.photo(photo)
        self.assertEqual(result, photo)

    def test_photo_with_invalid_suffix(self):
        invalid_photo = SimpleUploadedFile(
            'invalid_image.txt', 
            b'file_content', 
            content_type='text/plain'
        )
        with self.assertRaises(serializers.ValidationError):
            Validation.photo(invalid_photo)

    def test_photo_with_valid_suffix_but_invalid_data(self):
        invalid_photo = SimpleUploadedFile(
            'invalid_image.png', 
            b'not_really_an_image', 
            content_type='image/png'
        )
        with self.assertRaises(serializers.ValidationError):
            Validation.photo(invalid_photo)

    def test_order_by_with_valid_data(self):
        data = ['-name', 'calories']
        options = ['name', 'title', 'prep_time', 'calories']
        result = Validation.order_by(data, options)
        self.assertEqual(result, data)

    def test_order_by_with_invalid_data(self):
        data = ['-name', 'invalid']
        options = ['name', 'title', 'prep_time', 'calories']
        with self.assertRaises(serializers.ValidationError):
            Validation.order_by(data, options)

    def test_serializer_with_valid_data(self):
        data = {'name': 'Test Name', 'age': 25}
        ser = self.DummySerializer(data=data)
        result = Validation.serializer(ser)
        self.assertEqual(result, ser)

    def test_serializer_with_invalid_field_data(self):
        data = {'name': '', 'age': 'invalid'}
        ser = self.DummySerializer(data=data)
        with self.assertRaises(VerificationException) as context:
            Validation.serializer(ser)
        expected_errors = {
            'name': ['This field may not be blank.'],
            'age': ['A valid integer is required.']
        }
        self.assertEqual(context.exception.args[0], expected_errors)

    def test_serializer_with_non_field_error(self):
        data = {'name': 'Invalid Name', 'age': 25}
        ser = self.DummySerializer(data=data)
        with self.assertRaises(VerificationException) as context:
            Validation.serializer(ser)
        expected_errors = {'non_field_errors': ['Invalid Name']}
        self.assertEqual(context.exception.args[0], expected_errors)

    def test_is_limited_within_limit(self):
        for idx in range(5):
            Recipe.objects.create(
                user=self.user,
                name=f'Test Recipe {idx}', title='Test Recipe Title',
                prep_time=10, calories=100, submit_status=0, deny_message='',
            )
        result = Validation.is_limited(self.user, Recipe, limit=(10, 24))
        self.assertFalse(result)

    def test_is_limited_exceeds_limit(self):
        for idx in range(15):
            Recipe.objects.create(
                user=self.user,
                name=f'Test Recipe {idx}', title='Test Recipe Title',
                prep_time=10, calories=100, submit_status=0, deny_message='',
            )
        result = Validation.is_limited(self.user, Recipe, limit=(10, 24))
        self.assertTrue(result)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TestVerification(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            email='test@example.com', name='Test User',
            vcode=None, vcode_expiry=None,
            pcode=None, pcode_expiry=None
        )

    def test_verify_send(self):
        Verification.Email.send(self.user)
        Verification.PasswordReset.send(self.user)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.vcode)
        self.assertIsNotNone(self.user.vcode_expiry)
        self.assertGreater(self.user.vcode_expiry, utc_now())
        self.assertIsNotNone(self.user.pcode)
        self.assertIsNotNone(self.user.pcode_expiry)
        self.assertGreater(self.user.pcode_expiry, utc_now())
        email_record_count = EmailRecord.objects.filter(user=self.user).count()
        self.assertEqual(email_record_count, 2)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, Verification.VerificationStrings.title)
        expected_message = Verification.VerificationStrings.message.format(self.user.vcode)
        self.assertEqual(mail.outbox[0].body, expected_message)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        expected_message = Verification.ResetStrings.message.format(self.user.pk, self.user.pcode)
        self.assertEqual(mail.outbox[1].subject, Verification.ResetStrings.title)
        self.assertEqual(mail.outbox[1].body, expected_message)
        self.assertEqual(mail.outbox[1].to, [self.user.email])

    def test_verify_valid_code(self):
        self.user.vcode = django_crypto.get_random_string(length=25)
        self.user.pcode = django_crypto.get_random_string(length=25)
        self.user.vcode_expiry = utc_now() + timedelta(hours=Config.IssueFor.email_code)
        self.user.pcode_expiry = utc_now() + timedelta(hours=Config.IssueFor.email_code)
        self.user.save()
        self.assertTrue(Verification.Email.verify(self.user, self.user.vcode))
        self.assertTrue(Verification.PasswordReset.verify(self.user, self.user.pcode))

    def test_verify_invalid_code(self):
        self.user.vcode = django_crypto.get_random_string(length=25)
        self.user.pcode = django_crypto.get_random_string(length=25)
        self.user.vcode_expiry = utc_now() + timedelta(hours=Config.IssueFor.email_code)
        self.user.pcode_expiry = utc_now() + timedelta(hours=Config.IssueFor.email_code)
        self.user.save()
        self.assertFalse(Verification.Email.verify(self.user, 'invalid code'))
        self.assertFalse(Verification.PasswordReset.verify(self.user, 'invalid code'))

    def test_verify_expired_code(self):
        self.user.vcode = django_crypto.get_random_string(length=25)
        self.user.pcode = django_crypto.get_random_string(length=25)
        self.user.vcode_expiry = utc_now() - timedelta(hours=1)
        self.user.pcode_expiry = utc_now() - timedelta(hours=1)
        self.user.save()
        self.assertFalse(Verification.Email.verify(self.user, self.user.vcode))
        self.assertFalse(Verification.Email.verify(self.user, self.user.pcode))
