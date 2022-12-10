import logging
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework.response import Response
from rest_framework import status

log = logging.getLogger(__name__)



class BannedException(Exception):
    def __init__(self, message = None):
        self.message = message


class VerificationException(Exception):
    def __init__(self, errors):
        self.errors = errors


class ContentLimitException(Exception):
    def __init__(self, limit):
        self.limit = limit


def handler(ex, _):
    if isinstance(ex, VerificationException):
        return Response(data={'detail': ex.errors}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(ex, ContentLimitException):
        return Response(data={'detail': ex.limit}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(ex, PermissionDenied):
        return Response(data={}, status=status.HTTP_401_UNAUTHORIZED)
    if isinstance(ex, BannedException):
        return Response(data={'detail': "You have been banned."}, status=status.HTTP_403_FORBIDDEN)
    if isinstance(ex, Http404):
        return Response(data={}, status=status.HTTP_404_NOT_FOUND)
    log.error(f"Error - internal server error: {ex}")
    return Response(data={}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
