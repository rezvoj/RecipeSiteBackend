import jwt
from datetime import timedelta
from django.conf import settings
from django.http import HttpRequest
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from rest_framework.authentication import BaseAuthentication
from recipeAPIapp.apps import Config
from recipeAPIapp.utils.exception import BannedException
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.models.user import User



def generate_token(user: User, issue_for_days = Config.IssueFor.jwt_token):
    token = jwt.encode({
        'id': user.pk, 'di': user.details_iteration,
        'exp': utc_now() + timedelta(days=issue_for_days)
    }, settings.SECRET_KEY, algorithm='HS256')
    return token


def check_password(user: User, password: str):
    return PBKDF2PasswordHasher().verify(password, user.password_hash)


def set_password(user: User, password: str):
    salt = PBKDF2PasswordHasher().salt()
    user.password_hash = PBKDF2PasswordHasher().encode(password, salt)


class Authentication(BaseAuthentication):
    def authenticate(self, request: HttpRequest):
        auth_header: str = str(request.META.get('HTTP_AUTHORIZATION', ""))
        if not auth_header.startswith("Bearer "):
            return None, None
        try:
            token = auth_header[7:]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
        except jwt.InvalidTokenError:
            return None, None
        try:
            user = User.objects.get(pk=payload['id'])
        except User.DoesNotExist:
            return None, None
        if user.banned:
            raise BannedException()
        if payload['di'] != user.details_iteration:
            return None, None
        return user, None
