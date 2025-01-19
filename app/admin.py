from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Quiz, Question, Choice, Reference, Explanation, LearnerUser, UploadedFile

# Register your models here.
class LearnerUserAdmin(UserAdmin):
    model = LearnerUser
    list_display = ('email', 'nickname', 'first_name', 'last_name', 'experience_points', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'nickname')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'experience_points')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    search_fields = ('email', 'nickname', 'first_name', 'last_name')
    ordering = ('email',)

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(LearnerUser, LearnerUserAdmin)
admin.site.register(Reference)
admin.site.register(Explanation)
admin.site.register(UploadedFile)