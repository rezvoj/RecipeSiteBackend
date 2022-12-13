from django.conf import settings
from django.http import HttpRequest
from django.core.exceptions import PermissionDenied
from rest_framework.request import Request
from recipeAPIapp.models.user import User



def user(request: Request):
    user = request.user
    if not isinstance(user, User):
        raise PermissionDenied()
    return user


def verified(request: Request):
    user = request.user
    if not isinstance(user, User) or user.vcode is not None:
        raise PermissionDenied()
    return user


def is_admin(request: HttpRequest):
    code = request.META.get('HTTP_ADMINCODE', None)
    return code == settings.APP_ADMIN_CODE


def admin(request: Request):
    if not is_admin(request):
        raise PermissionDenied()
    return request.user


def is_admin_or_moderator(request: Request):
    user = request.user
    return is_admin(request) or (isinstance(user, User) and user.moderator)


def admin_or_moderator(request: Request):
    if not is_admin_or_moderator(request):
        raise PermissionDenied()
    return request.user


def user_id(request: Request):
    if is_admin(request):
        return 'admin'
    if not isinstance(request.user, User):
        return 'anon'
    return request.user.pk
