from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('glogin/', GLogin.as_view(), name='Glogin'),
    path('userProfile/', UserProfileView.as_view(), name='user-detail'),
    path('ForgotPassword/', ForgotPassword.as_view(), name='ForgotPassword'),
    path('VerifyEmail/', VerifyEmail.as_view(), name='VerifyEmail'),
    path('VerifyForgotPassword/', VerifyForgotPassword.as_view(), name='VerifyForgotPassword'),
    path('serverApi/', serverApi.as_view(), name='serverApi'),
]