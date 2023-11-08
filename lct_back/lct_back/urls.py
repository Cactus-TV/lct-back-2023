from django.contrib import admin
from django.urls import path, include

from django.conf.urls.static import static
from django.conf import settings
from back.views import *
from django.views.generic.base import TemplateView

urlpatterns = [
                  path("admin/", admin.site.urls),
                  path('contas/', include('django.contrib.auth.urls')),
                  path('back/', include('back.urls')),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)