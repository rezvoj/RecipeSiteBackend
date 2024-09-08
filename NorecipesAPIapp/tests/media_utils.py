import shutil
from pathlib import Path
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

TEST_MEDIA_ROOT = Path(__file__).resolve().parent.parent.parent / 'test_media/'
TEST_DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'



def generate_test_image(color: tuple = (0, 0, 0)):
    image = Image.new('RGB', (100, 100), color=color)
    byte_arr = BytesIO()
    image.save(byte_arr, format='JPEG')
    byte_arr.seek(0)
    return SimpleUploadedFile("photo.jpg", byte_arr.read(), content_type="image/jpeg")


def delete_test_media():
    if TEST_MEDIA_ROOT.exists() and TEST_MEDIA_ROOT.is_dir():
        shutil.rmtree(TEST_MEDIA_ROOT)
