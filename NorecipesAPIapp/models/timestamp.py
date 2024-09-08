from datetime import datetime, timezone
from django.db import models



def utc_now():
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)


class Timestamped(models.Model):
    created_at = models.DateTimeField(default=utc_now)
    class Meta:
        abstract = True


class EditTimestamped(models.Model):
    created_at = models.DateTimeField(default=utc_now)
    edited_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        abstract = True
