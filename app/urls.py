from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('app/', views.app, name='app'),
    path('profile/', views.profile, name='profile'),
    path('quizzes/', views.quizzes, name='quizzes'),
    path('shared', views.shared_quizzes, name='shared_quizzes'),
    path('friends/', views.friends, name='friends'),
    path('send-request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('accept-request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('decline-request/<int:request_id>/', views.decline_friend_request, name='decline_friend_request'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('signup/', views.signup_user, name='signup'),
    path('delete-account/', views.delete_user, name='delete_account'),
    path('quiz/<int:pk>', views.quiz, name='quiz'),
    path('delete-quiz/<int:pk>', views.delete_quiz, name='delete_quiz'),
    path('update-quiz/<int:pk>', views.update_quiz, name='update_quiz'),
    path('auth-receiver', views.auth_receiver, name='auth_receiver'),
    path('sign-out', views.sign_out, name='sign_out'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('password-change', views.password_change, name='password_change'),
    path("password-reset", views.password_reset_request, name="password_reset"),
    path('reset/<uidb64>/<token>', views.passwordResetConfirm, name='password_reset_confirm'),
    path('share-quiz/<int:quiz_id>/', views.share_with_all_friends, name='share_with_friends'),
    path('unshare-quiz/<int:quiz_id>/', views.unshare_quiz, name='unshare_quiz'),
    path('unfriend/<int:friend_id>/', views.unfriend, name='unfriend'),
] 
