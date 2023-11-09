from django.urls import path

from .views import *

urlpatterns = [
    path('stream/show/', StreamView.as_view(), name='stream'),
    path('transmition/', transmition, name='transmition'),
    path('frame/', frame, name='frame'),
    path('stream/frame/', FrameCreateAPI.as_view()),
    path('stream/get/', StreamAPIGet.as_view()),
    path('stream/update/<str:pk>/', StreamAPIUpdate.as_view()),
    path('stream/post/', StreamAPICreate.as_view()),
    path('stream/active/', StreamUpdateIsActiveAPI.as_view()),
]