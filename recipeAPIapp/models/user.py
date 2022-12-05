from django.db import models
from django.core.validators import MinLengthValidator
from recipeAPIapp.models.timestamp import Timestamped



class UserAuthentication(models.Model):
    password_hash = models.CharField(max_length=150, null=True, blank=True)
    details_iteration = models.IntegerField(default=1)
    banned = models.BooleanField(default=False)
    moderator = models.BooleanField(default=False)
    vcode = models.CharField(max_length=40, null=True, blank=True)
    vcode_expiry = models.DateTimeField(null=True, blank=True)
    pcode = models.CharField(max_length=40, null=True, blank=True)
    pcode_expiry = models.DateTimeField(null=True, blank=True)
    class Meta:
        abstract = True


class User(UserAuthentication, Timestamped):
    photo = models.ImageField(upload_to='user/', null=True, blank=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=75, validators=[MinLengthValidator(3)])
    about = models.CharField(max_length=500, null=True, blank=True)


class UserReport(Timestamped):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report')
    reported = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported')
    class Meta:
        unique_together = ('user', 'reported')


class EmailRecord(Timestamped):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emailrecord')
