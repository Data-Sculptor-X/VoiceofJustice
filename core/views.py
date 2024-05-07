from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.conf import settings
import random
import string
from rest_framework.permissions import IsAuthenticated, IsAuthenticated
from rest_framework.response import Response
import jwt
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
from accounts.models import *
import os
from dotenv import load_dotenv
load_dotenv()
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
        name_element = lawyer_box.find('h2', class_='media-heading')
        if name_element:
            lawyer_data['name'] = name_element.text.strip()
        else:
            lawyer_data['name'] = "Name Not Available"
        name_element2 = lawyer_box.find('div', class_='small-info')
        if name_element2:
            lawyer_data['name'] = name_element2.find('a')['title']
        # Get lawyer's rating and user ratings
        rating_element = lawyer_box.find('span', class_='score')
        if rating_element:
            rating_text = rating_element.text.strip().split('|')
            lawyer_data['rating'] = rating_text[0]
            lawyer_data['user_ratings'] = rating_text[1]
        else:
            lawyer_data['rating'] = "Rating Not Available"
            lawyer_data['user_ratings'] = "User Ratings Not Available"

        # Get location
        location_element = lawyer_box.find('div', class_='location')
        if location_element:
            lawyer_data['location'] = location_element.text.strip()
        else:
            lawyer_data['location'] = "Location Not Available"

        # Get experience
        experience_element = lawyer_box.find('div', class_='experience')
        if experience_element:
            lawyer_data['experience'] = experience_element.text.strip()
        else:
            lawyer_data['experience'] = "Experience Not Available"

        # Get practice area & skills
        practice_area_element = lawyer_box.find('div', class_='area-skill')
        if practice_area_element:
            lawyer_data['practice_area'] = practice_area_element.find('div').text.strip()
            
        else:
            lawyer_data['practice_area'] = "Practice Area Not Available"

        # Get image link
        image_link_element = lawyer_box.find('img')
        if image_link_element:
            lawyer_data['image_link'] = image_link_element['src']
        else:
            lawyer_data['image_link'] = "Image Link Not Available"

        # Get contact link
        contact_link_element = lawyer_box.find('div', class_='cta margin-small-top')
        if contact_link_element:
            lawyer_data['contact_link'] = contact_link_element.find('a')['href']
        else:
            lawyer_data['contact_link'] = "Contact Link Not Available"

        lawyers.append(lawyer_data)
    return lawyers

class GetLawyer(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):

        case = request.data.get('case', '')
        place = request.data.get('place', None)
        lang = request.data.get('lang', 'en')
        page = request.data.get('page', '2')
        print(case,place,page)
        if lang=="en":
            url_template = f"https://lawrato.com/{case}-lawyers{'/'+place if place else ''}?&page={page}"
        elif lang=="ta":
            url_template = f"https://tamil.lawrato.com/{case}-வழக்கறிஞர்கள்{'/'+place if place else ''}?&page={page}"
        elif lang=="hi":
            url_template = f"https://hindi.lawrato.com/{case}-वकील{'/'+place if place else ''}?&page={page}"
        lawyers_data = scrape_lawyers(url_template)
        print(url_template)
        return Response(lawyers_data)

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Law

class GetLaws(APIView):
    permission_classes = (IsAuthenticated,)

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
from rest_framework.permissions import IsAuthenticated
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

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
    url = f"https://api.datamuse.com/words?rel_syn={query}"
    response = requests.get(url)
    if response.status_code == 200:
        synonyms = set()
        data = response.json()
        for entry in data:
            synonyms.add(preprocess_text(entry['word']))
        return ' '.join(synonyms)
    else:
        return query


class GetQueryLaw(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        laws = Law.objects.all()
        data = [law.data for law in laws if law.data is not None]
        documents = [combine_text(doc) for doc in data]
        preprocessed_documents = [preprocess_text(doc) for doc in documents]

        vectorizer = TfidfVectorizer()
        documents_tfidf = vectorizer.fit_transform(preprocessed_documents)

        query = request.data.get('query', '')  # Assuming query is sent in the request data
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



from openai import OpenAI
class AI:
    def __init__(self):
        self.client = OpenAI(
            api_key= os.getenv('OPENAI_KEY'),
        )
        # self.context = ""
    def get_response(self, question,language):
        # if len(self.context) > 0:
        if language=="en":
            question =  question
        elif language=="ta":
            question =  question + " give response in tamil"
        elif language=="hi":
            question =  question + " give response in hindi"

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": question},
            ],
            max_tokens=4000,
        )

        self.context = response.choices[0].message.content
        return self.context


ai = AI()
class GenerateText2(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        prompt = request.data.get('prompt', '')
        language = request.data.get('lang', 'en')
        response = ai.get_response(prompt,language)  # Assuming `model` is defined elsewhere
        print(response)
        if response :
            sectionID = request.data.get('SectionID', '')
            if sectionID:
                    section = SectionHistory.objects.get(SectionID=sectionID)
                    ChatHistory.objects.create(
                        SectionID=section,
                        ChatQuestion=prompt,
                        ChatResponse=response
                    )
                    return Response({'generated_text': response,"SectionID":sectionID})
            
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
                        ChatResponse=response
                    )
                    return Response({'generated_text': response,"SectionID":sect})
                else:
                    return Response({'error': 'Section not found.'}, status=400)

        else:
            return Response({'error': 'Empty response from the model.'}, status=400)

