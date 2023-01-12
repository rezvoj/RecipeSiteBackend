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


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TestVerification(APITestCase):
    def setUp(self):
        self.user = User(email="test@example.com", name="Test User")
        security.set_password(self.user, "testpassword")
        self.user.vcode = "verification_code"
        self.user.vcode_expiry = utc_now() + timedelta(hours=1)
        self.user.save()
        self.token = security.generate_token(self.user)

    def test_resend_verification_email(self):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.post(
            '/auth/email-verification', 
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        previous_vcode = self.user.vcode
        previous_vcode_expiry = self.user.vcode_expiry
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.vcode)
        self.assertNotEqual(self.user.vcode, previous_vcode)
        self.assertIsNotNone(self.user.vcode_expiry)
        self.assertNotEqual(self.user.vcode_expiry, previous_vcode_expiry)

    def test_verification_email_limit(self):
        limit = Config.ContentLimits.email_code
        for _ in range(limit[0]):
            EmailRecord.objects.create(user=self.user)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.post(
            '/auth/email-verification', 
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'limit': limit[0], 'hours': limit[1]}}
        self.assertEqual(response.data, expected_data)
        previous_vcode = self.user.vcode
        previous_vcode_expiry = self.user.vcode_expiry
        self.user.refresh_from_db()
        self.assertEqual(self.user.vcode, previous_vcode)
        self.assertEqual(self.user.vcode_expiry, previous_vcode_expiry)

    def test_complete_verification(self):
        verification_code = self.user.vcode
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.put(
            f'/auth/email-verification/{verification_code}', 
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.vcode)
        self.assertIsNone(self.user.vcode_expiry)

    def test_complete_verification_invalid_code(self):
        invalid_code = "invalid_code"
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.put(
            f'/auth/email-verification/{invalid_code}', 
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'non_field_errors': ['invalid email verification code.']}}
        self.assertEqual(response.data, expected_data)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.vcode)
        self.assertIsNotNone(self.user.vcode_expiry)

    def test_complete_verification_already_verified(self):
        self.user.vcode = None
        self.user.vcode_expiry = None
        self.user.save()
        verification_code = "some_code"
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        response: Response = self.client.put(
            f'/auth/email-verification/{verification_code}', 
            format='json', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'non_field_errors': ['email already verified.']}}
        self.assertEqual(response.data, expected_data)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TestPasswordReset(APITestCase):    
    def setUp(self):
        self.user = User(email="test@example.com", name="Test User")
        security.set_password(self.user, "testpassword")
        self.user.pcode = "password_reset_code"
        self.user.pcode_expiry = utc_now() + timedelta(hours=1)
        self.user.save()

    def test_send_password_reset_email(self):
        response: Response = self.client.post(
            '/auth/password-reset', 
            data={"email": "test@example.com"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        previous_pcode = self.user.pcode
        previous_pcode_expiry = self.user.pcode_expiry
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.pcode)
        self.assertNotEqual(self.user.pcode, previous_pcode)
        self.assertIsNotNone(self.user.pcode_expiry)
        self.assertNotEqual(self.user.pcode_expiry, previous_pcode_expiry)

    def test_password_reset_email_limit(self):
        limit = Config.ContentLimits.email_code
        for _ in range(limit[0]):
            EmailRecord.objects.create(user=self.user)
        response: Response = self.client.post(
            '/auth/password-reset', 
            data={"email": "test@example.com"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'limit': limit[0], 'hours': limit[1]}}
        self.assertEqual(response.data, expected_data)
        previous_pcode = self.user.pcode
        previous_pcode_expiry = self.user.pcode_expiry
        self.user.refresh_from_db()
        self.assertEqual(self.user.pcode, previous_pcode)
        self.assertEqual(self.user.pcode_expiry, previous_pcode_expiry)

    def test_verify_password_reset_code(self):
        response: Response = self.client.get(
            f'/auth/password-reset/{self.user.pk}/{self.user.pcode}',
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_invalid_password_reset_code(self):
        invalid_code = "invalid_code"
        response: Response = self.client.get(
            f'/auth/password-reset/{self.user.pk}/{invalid_code}',
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'non_field_errors': ['invalid password reset code.']}}
        self.assertEqual(response.data, expected_data)

    def test_complete_password_reset(self):
        new_password = "new$$password"
        previous_di = self.user.details_iteration
        response: Response = self.client.put(
            f'/auth/password-reset/{self.user.id}/{self.user.pcode}',
            data={"password": new_password},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.user.refresh_from_db()
        self.assertTrue(security.check_password(self.user, new_password))
        self.assertEqual(self.user.details_iteration, previous_di + 1)
        self.assertIsNone(self.user.pcode)
        self.assertIsNone(self.user.pcode_expiry)

    def test_complete_password_reset_invalid_code(self):
        invalid_code = "invalid_code"
        new_password = "newpassword"
        previous_password_hash = self.user.password_hash
        previous_di = self.user.details_iteration
        response: Response = self.client.put(
            f'/auth/password-reset/{self.user.pk}/{invalid_code}',
            data={"password": new_password},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'non_field_errors': ['invalid password reset code.']}}
        self.assertEqual(response.data, expected_data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.password_hash, previous_password_hash)
        self.assertEqual(self.user.details_iteration, previous_di)
        self.assertIsNotNone(self.user.pcode)
        self.assertIsNotNone(self.user.pcode_expiry)

    def test_invalid_user_id(self):
        invalid_user_id = 9999
        verification_code = self.user.pcode
        response: Response = self.client.get(
            f'/auth/password-reset/{invalid_user_id}/{verification_code}',
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_data = {'detail': {'non_field_errors': ['invalid password reset code.']}}
        self.assertEqual(response.data, expected_data)
        response: Response = self.client.put(
            f'/auth/password-reset/{invalid_user_id}/{verification_code}',
            data={"password": "newpassword"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_data)
