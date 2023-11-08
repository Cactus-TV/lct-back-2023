from django.urls import path

from .views import *

urlpatterns = [
    path('stream/', StreamView.as_view(), name='stream'),
    path('transmition/', transmition, name='transmition'),
]