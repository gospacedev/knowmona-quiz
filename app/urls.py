from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('app/', views.app, name='app'),
    path('profile/', views.profile, name='profile'),
    path('quizzes/', views.quizzes, name='quizzes'),
    path('bites/', views.bites, name='bites'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('signup/', views.signup_user, name='signup'),
    path('quiz/<int:pk>', views.quiz, name='quiz'),
    path('delete-quiz/<int:pk>', views.delete_quiz, name='delete_quiz'),
    path('update-quiz/<int:pk>', views.update_quiz, name='update_quiz'),
    path('auth-receiver', views.auth_receiver, name='auth_receiver'),
    path('sign-out', views.sign_out, name='sign_out'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('quiz/<int:quiz_id>/status/', views.quiz_status, name='quiz_status'),
    path('quiz/<int:quiz_id>/check_status/', views.check_quiz_status, name='check_quiz_status'),
] 
