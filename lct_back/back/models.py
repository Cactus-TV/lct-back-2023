from django.db import models
import uuid

class Stream(models.Model): #стрим
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    stream_name = models.CharField(max_length=128, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=512, unique=True)
    username = models.CharField(max_length=128)
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.uid