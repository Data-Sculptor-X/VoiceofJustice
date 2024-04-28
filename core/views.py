from rest_framework.decorators import api_view
from rest_framework.response import Response
import google.generativeai as genai
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.conf import settings
import random
import string
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import jwt
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
from accounts.models import *
# Configure the model
genai.configure(api_key='AIzaSyCLfi0mijR7Xf4fvGvHRINxz5UiQYULaq8')
model = genai.GenerativeModel(model_name='models/gemini-pro')

verification_key_path = settings.PUBLIC_KEY_PATH
try:
    verification_key = open(settings.PUBLIC_KEY_PATH, 'r').read()
except FileNotFoundError:
    print(f"Error: Public key file not found at {settings.PUBLIC_KEY_PATH}")
   
def generate_random_string(username,length):
    letters_and_digits = string.ascii_uppercase + string.digits
    data =''.join(random.choice(letters_and_digits) for _ in range(length))
    return str(username)+data

def trim_sentence(sentence):
    if len(sentence) > 40:
        return sentence[:40]
    return sentence

class GenerateText(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        prompt = request.data.get('prompt', '')
        response = model.generate_content(prompt)  # Assuming `model` is defined elsewhere

        if response and response.text:
            sectionID = request.data.get('SectionID', '')
            if sectionID:
                    section = SectionHistory.objects.get(SectionID=sectionID)
                    ChatHistory.objects.create(
                        SectionID=section,
                        ChatQuestion=prompt,
                        ChatResponse=response.text
                    )
                    return Response({'generated_text': response.text,"SectionID":sectionID})
            
            else:

                jwt_object = JWTAuthentication() 
                token = jwt_object.get_raw_token(jwt_object.get_header(request))  
                try:
                    data = jwt.decode(token, verification_key, algorithms=["RS256"])
                except UnicodeDecodeError as e:
                    print(f"UnicodeDecodeError: {e}")
                    print(f"Problematic token: {token}")
                    print(data)

                userTrackData = UserTrack.objects.get(id=data["tk"])


                sect=generate_random_string(userTrackData.username,10)
                section = SectionHistory.objects.create(
                                                    SectionID=sect,
                                                    username=userTrackData.username,
                                                    SectionName=trim_sentence(prompt)
                                                        )
                if section:
                    ChatHistory.objects.create(
                        SectionID=section,
                        ChatQuestion=prompt,
                        ChatResponse=response.text
                    )
                    return Response({'generated_text': response.text,"SectionID":sect})
                else:
                    return Response({'error': 'Section not found.'}, status=400)

        else:
            return Response({'error': 'Empty response from the model.'}, status=400)


class GetSection(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            jwt_object = JWTAuthentication() 
            token = jwt_object.get_raw_token(jwt_object.get_header(request))  
            data = jwt.decode(token, verification_key, algorithms=["RS256"])
            userTrackData = UserTrack.objects.get(id=data["tk"])
            section_data = SectionHistory.objects.filter(username=userTrackData.username).order_by('-TimeStamp')
            serialized_data = []
            for section in section_data:
                serialized_data.append({
                    "SectionID": section.SectionID,
                    "SectionName": section.SectionName,
                    "TimeStamp": section.TimeStamp
                })
            return Response(serialized_data)
        except UnicodeDecodeError as e:
            return Response({"error": "UnicodeDecodeError", "message": str(e)}, status=500)
        except Exception as e:
            return Response({"error": "Exception", "message": str(e)}, status=500)



class GetChat(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            SectionId = request.data.get('SectionID', '')
            chat_data = ChatHistory.objects.filter(SectionID__SectionID=SectionId).order_by('-TimeStamp')
            serialized_data = []
            for chat in chat_data:
                serialized_data.append({
                    "SectionID": chat.SectionID.SectionID,  # Serialize only SectionID
                    "ChatQuestion": chat.ChatQuestion,
                    "ChatResponse": chat.ChatResponse,
                    "TimeStamp": chat.TimeStamp
                })
            return Response(serialized_data)
        except UnicodeDecodeError as e:
            return Response({"error": "UnicodeDecodeError", "message": str(e)}, status=500)
        except Exception as e:
            return Response({"error": "Exception", "message": str(e)}, status=500)

