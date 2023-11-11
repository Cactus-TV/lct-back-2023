from django.db import models
import uuid
import os
from dotenv import load_dotenv

load_dotenv()
MEDIA_PATH = os.environ.get('MEDIA_PATH')

class Stream(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    stream_name = models.CharField(max_length=128, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=512, unique=True)
    username = models.CharField(max_length=128)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.uid


class Frame(models.Model): #screenshots
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    frame = models.ImageField(upload_to=MEDIA_PATH)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uid