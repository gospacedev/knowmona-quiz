from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Quiz, Question, Choice, Reference, Explanation, LearnerUser, UploadedFile, UserEnergy, Suggestion

# Register your models here.


@admin.register(LearnerUser)
class LearnerUserAdmin(UserAdmin):
    model = LearnerUser
    list_display = ['email', 'nickname', 'first_name',
                    'last_name', 'date_joined', 'experience_points', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('email', 'password', 'nickname')}),
        ('Personal Info', {
         'fields': ('first_name', 'last_name', 'experience_points')}),
        ('Permissions', {'fields': ('is_staff',
         'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    search_fields = ['email', 'nickname', 'first_name', 'last_name']
    ordering = ['email']


@admin.register(UserEnergy)
class UserEnergyAdmin(admin.ModelAdmin):
    list_display = ['user', 'energy', 'last_reset']
    list_filter = ['user']


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ['topic', 'order']
    list_editable = ['order']


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'file', 'uploaded_at']
    list_filter = ['quiz']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['topic', 'tone', 'question_difficulty', 'user', 'created_at']
    list_filter = ['user']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz']
    list_filter = ['quiz']


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['text', 'question']
    list_filter = ['question']


@admin.register(Explanation)
class ExplanationAdmin(admin.ModelAdmin):
    list_display = ['text', 'question']
    list_filter = ['question']


@admin.register(Reference)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz']
    list_filter = ['quiz']
