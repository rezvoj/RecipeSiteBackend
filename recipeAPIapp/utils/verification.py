import django.core.mail as mail
import django.utils.crypto as django_crypto
from datetime import timedelta
from recipeAPIapp.apps import Config
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.models.user import User, EmailRecord



class VerificationStrings:
    title = "Recipe App - Email Verification"
    message = """Please verify your email address by clicking the following link:
        www.fakerecipeapp.com/auth/email-verification/{}"""


class ResetStrings:
    title = "Recipe App - Password reset"
    message = """Reset your password by clicking the following link:
        www.fakerecipeapp.com/auth/password-reset/{}/{}"""


class Email:
    def send(user: User):
        user.vcode = django_crypto.get_random_string(length=25)
        user.vcode_expiry = utc_now() + timedelta(hours=Config.IssueFor.email_code)
        user.save()
        EmailRecord(user=user).save()
        message = VerificationStrings.message.format(user.vcode)
        mail.send_mail(VerificationStrings.title, message, None, [user.email])

    def verify(user: User, code: str):
        if user.vcode != code or user.vcode_expiry <= utc_now():
            return False
        return True


class PasswordReset:
    def send(user: User):
        user.pcode = django_crypto.get_random_string(length=25)
        user.pcode_expiry = utc_now() + timedelta(hours=Config.IssueFor.email_code)
        user.save()
        EmailRecord(user=user).save()
        message = ResetStrings.message.format(user.pk, user.pcode)
        mail.send_mail(ResetStrings.title, message, None, [user.email])

    def verify(user: User, code: str):
        if user.pcode != code or user.pcode_expiry <= utc_now():
            return False
        return True
