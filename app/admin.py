from django.contrib import admin
from .models import Quiz, Question, Choice, Reference, Explanation, LearnerUser


# Register your models here.

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(LearnerUser)
admin.site.register(Reference)
admin.site.register(Explanation)