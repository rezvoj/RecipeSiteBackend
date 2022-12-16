from datetime import timedelta
from PIL import Image, UnidentifiedImageError
from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.utils.exception import VerificationException



def photo(photo: UploadedFile):
    if photo is not None:
        try:
            with Image.open(photo) as img:
                img.verify()
        except UnidentifiedImageError:
            raise serializers.ValidationError("photo file is not an image.")
    return photo


def order_by(data: list[str], options: list[str]):
    new_options = set(options + [f'-{option}' for option in options])
    for param in data:
        if param not in new_options:
            raise serializers.ValidationError("invalid ordering parameters.")
    return data


def serializer(ser: serializers.Serializer):
    if not ser.is_valid():
        errors = {key: [str(err) for err in value] for key, value in ser.errors.items()}
        raise VerificationException(errors)
    return ser


def is_limited(user, type, limit):
    start_date = utc_now() - timedelta(hours=limit[1])
    return type.objects.filter(user=user, created_at__gte=start_date).count() >= limit[0]
