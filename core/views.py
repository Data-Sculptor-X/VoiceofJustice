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
import json
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



from bs4 import BeautifulSoup
import requests
import json

def scrape_lawyers(url):
    lawyers = []
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    lawyer_boxes = soup.find_all('div', class_='lawyer-item')

    for lawyer_box in lawyer_boxes:
        lawyer_data = {}

        # Get lawyer's name
        lawyer_data['name'] = lawyer_box.find('h2', class_='media-heading').text.strip()

        # Get lawyer's rating
        rating = lawyer_box.find('span', class_='score').text.split('|')[0].strip()
        lawyer_data['rating'] = rating

        # Get number of user ratings
        user_ratings = lawyer_box.find('span', class_='score').text.split('|')[1].strip()
        lawyer_data['user_ratings'] = user_ratings

        # Get location
        location = lawyer_box.find('div', class_='location').text.strip()
        lawyer_data['location'] = location

        # Get experience
        experience = lawyer_box.find('div', class_='experience').text.strip()
        lawyer_data['experience'] = experience

        # Get practice area & skills
        practice_area = lawyer_box.find('div', class_='area-skill').text.strip()
        lawyer_data['practice_area'] = practice_area

        # Get image link
        image_link = lawyer_box.find('img')['src']
        lawyer_data['image_link'] = image_link
        contact_link = lawyer_box.find('div', class_='cta margin-small-top')
        contact_link2 = contact_link.find('a')['href']
        lawyer_data['contact_link'] = contact_link2

        lawyers.append(lawyer_data)
    return lawyers
class GetLawyer(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):

        case = request.data.get('case', '')
        place = request.data.get('place', None)
        page = request.data.get('page', '2')
        if place:
            url_template = "https://lawrato.com/{case}/{place}?&page={page}".format(page=page,place=place,case=case)
        else:
            url_template = "https://lawrato.com/{case}?&page={page}".format(page=page,case=case)
        lawyers_data = scrape_lawyers(url_template)
        return Response(lawyers_data)

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .models import Law

class GetLaws(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        laws = Law.objects.all()
        paginator = Paginator(laws, 20)  # 20 laws per page
        page  = request.data.get('page', '')

        try:
            laws_page = paginator.page(page)
        except PageNotAnInteger:
            laws_page = paginator.page(1)
        except EmptyPage:
            laws_page = paginator.page(paginator.num_pages)

        data_list = [law.data for law in laws_page if law.data is not None]
        return JsonResponse(data_list, safe=False)









from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import re


nltk.download('wordnet')

def preprocess_text(text):
    if isinstance(text, str):
        text = re.sub(r'\W', ' ', text)  # Remove non-word characters
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespaces
        text = text.lower()  # Convert to lowercase
        return text
    else:
        return ''

def combine_text(doc):
    combined_text = ''
    for key, value in doc.items():
        if isinstance(value, dict):
            for k, v in value.items():
                combined_text += preprocess_text(v) + ' '
        elif isinstance(value, list):
            combined_text += ' '.join([preprocess_text(sub_value) for sub_value in value]) + ' '
        else:
            combined_text += preprocess_text(str(value)) + ' '  # Convert non-string values to string
    return combined_text

def expand_query_with_synonyms(query):
    synonyms = set()
    for syn in nltk.corpus.wordnet.synsets(query):
        for lemma in syn.lemmas():
            synonyms.add(preprocess_text(lemma.name()))
    return ' '.join(synonyms)

class GetQueryLaw(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        laws = Law.objects.all()
        data = [law.data for law in laws if law.data is not None]

        # Combine text from all fields for each document
        documents = [combine_text(doc) for doc in data]
        # Preprocess documents
        preprocessed_documents = [preprocess_text(doc) for doc in documents]

        vectorizer = TfidfVectorizer()
        documents_tfidf = vectorizer.fit_transform(preprocessed_documents)

        query = request.data.get('query', '')  # Assuming query is sent in the request data
        expanded_query = expand_query_with_synonyms(query)
        print(expanded_query)
        query_vector = vectorizer.transform([query])
        cosine_similarities = cosine_similarity(query_vector, documents_tfidf).flatten()
        
        top_indices = cosine_similarities.argsort()[-5:][::-1]
        results = []
        for idx in top_indices:
            results.append(data[idx])
        
        if results:
            return Response(results)
        else:
            return Response({'message': 'No results found'})
