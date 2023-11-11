from django.urls import path

from .views import *

urlpatterns = [
    path('stream/', StreamView.as_view(), name='stream'),
    path('transmition/', transmition, name='transmition'),
    path('frame/get/', frame, name='frame'),
    path('frame_detected/get/', frame_detected, name='frame_detected'),
    path('stream/frame/create/', FrameCreateAPI.as_view()),
    path('stream/get/', StreamAPIGet.as_view()),
    path('stream/update/<str:pk>/', StreamAPIUpdate.as_view()),
    path('stream/post/', StreamAPICreate.as_view()),
    path('stream/active/', StreamUpdateIsActiveAPI.as_view()),
]