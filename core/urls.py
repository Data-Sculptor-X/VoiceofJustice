from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings

from django.urls import path
from .views import *

urlpatterns = [
    path('generate/', GenerateText.as_view(), name='generate_text'),
    path('getSection/', GetSection.as_view(), name='getSection'),
    path('getChat/', GetChat.as_view(), name='getChat'),
]
