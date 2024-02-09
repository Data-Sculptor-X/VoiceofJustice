# pull official base image
FROM python:3.8
ENV PYTHONUNBUFFERED 1
RUN pip install --upgrade pip
WORKDIR /voiceofjustice
COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY . /voiceofjustice/
RUN python manage.py collectstatic --no-input
