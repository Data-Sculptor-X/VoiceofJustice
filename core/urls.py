from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings

from django.urls import path
from core import views

urlpatterns = [
    path('generate/', views.generate_text, name='generate_text'),
]
