from django.contrib import admin

# Register your models here.
from .models import *

class SectionHistoryClass(admin.ModelAdmin):
	list_display = ('username','SectionID','SectionName','TimeStamp')
admin.site.register(SectionHistory,SectionHistoryClass)
class ChatHistoryClass(admin.ModelAdmin):
	list_display = ('id','SectionID','ChatQuestion','TimeStamp')
admin.site.register(ChatHistory,ChatHistoryClass)
admin.site.register(Lawyer)
admin.site.register(News)
admin.site.register(Law)