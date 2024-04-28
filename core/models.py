from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class SectionHistory(models.Model):
	username = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)  
	SectionID = models.CharField(max_length=255, null=True,blank=True)  
	SectionName = models.CharField(max_length=255, null=True,blank=True)  
	TimeStamp =  models.DateTimeField(auto_now_add=True)  

	
class ChatHistory(models.Model):
	SectionID = models.ForeignKey(SectionHistory, on_delete=models.CASCADE,null=True,blank=True)  
	ChatQuestion = models.TextField( null=True,blank=True)  
	ChatResponse = models.TextField( null=True,blank=True)  
	TimeStamp =  models.DateTimeField(auto_now_add=True)  
	


class Lawyer(models.Model):
	name = models.CharField(max_length=255, null=True,blank=True)  
	court = models.CharField(max_length=255, null=True,blank=True)  
	Specialist = models.CharField(max_length=255, null=True,blank=True)  
	data =  models.JSONField( null=True,blank=True)  

class News(models.Model):
	date = models.DateField(null=True,blank=True)  
	data =  models.JSONField( null=True,blank=True)  

class Law(models.Model):
	act = models.CharField(max_length=255, null=True,blank=True)  
	actName = models.CharField(max_length=255, null=True,blank=True)  
	description = models.TextField(null=True,blank=True)  
	data =  models.JSONField( null=True,blank=True)  
