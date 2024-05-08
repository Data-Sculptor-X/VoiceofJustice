# your_app/views.py

from rest_framework import generics, permissions

from google.auth.transport import requests
from google.oauth2 import id_token
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import  LoginSerializer, UserSerializer
import jwt
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import *
from datetime import datetime
import calendar
import random
import string
from django.template import Context, Template
from django.core.mail import send_mail
import random
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import urllib.parse
from django.utils import timezone

User = get_user_model()
verification_key_path = settings.PUBLIC_KEY_PATH
try:
    verification_key = open(settings.PUBLIC_KEY_PATH, 'r').read()
except FileNotFoundError:
    pass
def generate_random_string(length):
    letters_and_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))



def sendGmail(data,type,to_email,subject):
    tempData = EmailTemplate.objects.get(name=type)
    template = Template(tempData.html)
    context = Context(data)
    message = template.render(context)
    subject = subject
    from_email = 'datasculptorx@gmail.com'
    recipient_list = [to_email]
    master = send_mail(subject, message, from_email, recipient_list, html_message=message)
    return "ok"

def user_type(UserProfileData):
    if UserProfileData.google_user:
        return "google"
    if UserProfileData.voj_user:
        return "voj"
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class VerifyForgotPassword(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        data = request.data
        password = data.get("password")
        otp = data.get("otp")
        sso = data.get("sso")
        key = b'OMtWIu8M2NodZzHVy9_AAaRwXyuCm7l0MbOiDZXQtyE='
        cipher_suite = Fernet(key)
        encrypted_string = urllib.parse.unquote(sso)
        decrypted_string = cipher_suite.decrypt(encrypted_string.encode()).decode()
        # Check if the email already exists
        try:
            user = User.objects.get(email=decrypted_string)
            userProfile = UserProfile.objects.get(
                username=user,
           
            )
            if userProfile.otp!=int(otp):
                return Response({"error": "Invalid OTP"}, status=500)
            elif userProfile.exp_date<timezone.now():
                return Response({"error": "OTP Expired"}, status=500)
            else:
                user.set_password(password)
                user.save()
            return Response({"message": "Password Recovered Successfully"}, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

class ForgotPassword(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        data = request.data
        email = data.get("email")
        # Check if the email already exists
        if UserProfile.objects.filter(email=email,google_user=True).exists():
            return Response({"error": "An account with this email already exists in Google Login."}, status=400)
        if not UserProfile.objects.filter(email=email,voj_user=True).exists():
            return Response({"error": "An account with this email not exists."}, status=400)


        try:
            user = User.objects.get( email=email)
            otp=random.randint(10000, 99999)
            userProfile = UserProfile.objects.get(
                username=user,
            )
            userProfile.otp=otp
            userProfile.exp_date = datetime.now() + timedelta(minutes=5, seconds=10)
            userProfile.save()
            key = b'OMtWIu8M2NodZzHVy9_AAaRwXyuCm7l0MbOiDZXQtyE='
            cipher_suite = Fernet(key)
            string_to_encrypt = email
            encrypted_string = cipher_suite.encrypt(string_to_encrypt.encode())
            encrypted_url_safe = urllib.parse.quote(encrypted_string)
            data={
                    "name":userProfile.name,
                    "otp":otp,
                    'encrypted_link':"https://www.voiceofjustice.me/verifyPassword?sso={}".format(encrypted_url_safe)
                }
            sendGmail(data,'otp',email,"Reset Your Password: One-Time Passcode (OTP) Included")

            return Response({"message": "OTP Sended Successfully"}, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

class VerifyEmail(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        data = request.data
        sso = data.get("sso")
        key = b'OMtWIu8M2NodZzHVy9_AAaRwXyuCm7l0MbOiDZXQtyE='
        cipher_suite = Fernet(key)
        
        encrypted_string = urllib.parse.unquote(sso)
        decrypted_string = cipher_suite.decrypt(encrypted_string.encode()).decode()
        try:
            userProfile = UserProfile.objects.get(
                email=decrypted_string,
            )
            userProfile.email_verified=True
            userProfile.save()
            data={
                    "username":userProfile.name,
                }
            sendGmail(data,'signUp',decrypted_string,'Welcome to Voice of Justice')

            return Response({"message": "Account Verified Successfully"}, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)



class RegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        data = request.data
        name = data.get("name")
        dob = data.get("dob")
        email = data.get("email")
        password = data.get("password")

        # Check if the email already exists
        if UserProfile.objects.filter(email=email,voj_user=True).exists():
            return Response({"error": "An account with this email already exists."}, status=400)
        if UserProfile.objects.filter(email=email,google_user=True).exists():
            return Response({"error": "An account with this email already exists in Google Login."}, status=400)
        try:
            current_datetime = datetime.now()
            timestamp = calendar.timegm(current_datetime.utctimetuple())
            user = User.objects.create(username="voj"+str(timestamp)+"D", email=email)
            user.set_password(password)
            user.save()

            userProfile = UserProfile.objects.create(
                username=user,
                voj_user=True,
                dob=dob,
                name=name,
                email=email,
                secret_key=generate_random_string(60)
            )
            userProfile.save()
            key = b'OMtWIu8M2NodZzHVy9_AAaRwXyuCm7l0MbOiDZXQtyE='
            cipher_suite = Fernet(key)
            string_to_encrypt = email
            encrypted_string = cipher_suite.encrypt(string_to_encrypt.encode())
            encrypted_url_safe = urllib.parse.quote(encrypted_string)
            data={
            "username":name,
            'encrypted_link':"https://www.voiceofjustice.me/verifyEmail?sso={}".format(encrypted_url_safe)
            }
            sendGmail(data,'verify',email,"Verify Your Account")
            return Response({"message": "Account created successfully."}, status=201)

        except Exception as e:
            user.delete()
            return Response({"error": str(e)}, status=500)


class GLogin(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        data = request.data
        token = data.get("token")


        try:
            ginfo = id_token.verify_oauth2_token(token, requests.Request(), "439800211520-e23qodk9aeoq6k2pk3ss43g22aiv61hp.apps.googleusercontent.com")
        except Exception as e:
                return Response({"error": str(e)}, status=500)
        

        email= ginfo.get('email')
        name= ginfo.get('name')


        # Check if the email already exists
        if UserProfile.objects.filter(email=email,google_user=True).exists():
            user = User.objects.get(email=email)
            user_track = UserTrack( 
                username=user,
                count= "1"
            )
            user_track.save()
            token = MyTokenObtainPairSerializer.get_token(user,user_track.id)
            success_data = {
                'refresh_token': str(token),
                'access_token': str(token.access_token)
            }
            return Response(success_data, status=201)
        elif UserProfile.objects.filter(email=email).exists():
            return Response({"error": "Account is already created with voj Login"}, status=500)
        else:
            try:
                current_datetime = datetime.now()
                timestamp = calendar.timegm(current_datetime.utctimetuple())
                user = User.objects.create(username="voj"+str(timestamp)+"G", email=email)
                user.set_password(generate_random_string(15))
                user.save()

                userProfile = UserProfile.objects.create(
                    username=user,
                    google_user=True,
                    email_verified=True,
                    name=name,
                    email=email,
                    secret_key=generate_random_string(60)
                )
                userProfile.save()
                user_track = UserTrack( 
                username=user,
                count= "1"
                )
                user_track.save()
                token = MyTokenObtainPairSerializer.get_token(user,user_track.id)
                success_data = {
                'refresh_token': str(token),
                'access_token': str(token.access_token),
                "first_login" :True
                }
                data={
                    "username":name
                }
                sendGmail(data,'signUp',email,'Welcome to Voice of Justice')
                return Response(success_data, status=201)

            except Exception as e:
                user.delete()
                return Response({"error": str(e)}, status=500)



class UserProfileView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request,format=None):
        jwt_object = JWTAuthentication() 
        token = jwt_object.get_raw_token(jwt_object.get_header(request))  
        try:
            data = jwt.decode(token, verification_key, algorithms=["RS256"])
        except UnicodeDecodeError as e:
            pass

        userTrackData = UserTrack.objects.get(id=data["tk"])
        UserProfileData = UserProfile.objects.get(username=userTrackData.username)
        userType=user_type(UserProfileData)
        user = userTrackData.username
        success_data = {
            "name":UserProfileData.name,
            "username":user.username,
            "dob":UserProfileData.dob,
            "email":UserProfileData.email,
            "phone_no":UserProfileData.phone_no,
            "user_type":userType,
            "profile_picture":UserProfileData.profile_picture.url if UserProfileData.profile_picture else None,
        }
        
        return Response(success_data)
    

class serverApi(APIView):
    def get(self, request,format=None):
        return Response("success")
