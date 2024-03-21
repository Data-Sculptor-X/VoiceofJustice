from rest_framework.decorators import api_view
from rest_framework.response import Response
import google.generativeai as genai

# Configure the model
genai.configure(api_key='AIzaSyCLfi0mijR7Xf4fvGvHRINxz5UiQYULaq8')
model = genai.GenerativeModel(model_name='models/gemini-pro')


@api_view(['POST'])
def generate_text(request):
    if request.method == 'POST':
        prompt = request.data.get('prompt', '')
        print(prompt)
        response = model.generate_content(prompt)
        print(response)

        return Response({'generated_text': response.text})
    else:
        return Response({'error': 'Only POST requests are allowed.'}, status=400)
