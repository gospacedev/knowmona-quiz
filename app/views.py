from multiprocessing.pool import AsyncResult
from PyPDF2 import PdfReader
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from docx import Document
from google.auth.transport import requests
from google.oauth2 import id_token
from django.views.decorators.csrf import csrf_exempt
import os
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import LearnerUser, Quiz, Question, Choice, Reference, Explanation, UploadedFile
from .forms import SignUpLearnerUser, QuizForm, UpdateQuestionFormSet, UpdateChoiceFormSet, ProfileForm
from .utils import infer_quiz_json, save_quiz_from_json
from django.contrib.auth import login
from django.shortcuts import render, redirect
from dotenv import load_dotenv
import time

from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage

from django.contrib.auth import get_user_model

from .tokens import account_activation_token

from .tasks import create_quiz, process_uploaded_file

load_dotenv()


def home(request):
    if request.user.is_authenticated:
        return redirect('app')
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def contact(request):
    return render(request, "contact.html")


def app(request):
    nickname = None

    if request.user.is_authenticated:
        nickname = getattr(request.user, 'nickname', None)
        quiz_form = QuizForm(
            initial={'question_difficulty': 'Average', 'tone': 'Casual'})

        if request.method == 'POST':
            quiz_form = QuizForm(request.POST)
            if quiz_form.is_valid():
                quiz = quiz_form.save(commit=False)
                quiz.user = request.user

                quiz.save()

                # Handle file uploads
                files = request.FILES.getlist('files')
                uploaded_texts = []

                for file in files:
                    try:
                        uploaded_file = UploadedFile(quiz=quiz, file=file)
                        uploaded_file.save()

                        file_handle = uploaded_file.file.open()
                        file_extension = os.path.splitext(file.name)[1].lower()

                        if file_extension == '.txt':
                            uploaded_texts.append(
                                file_handle.read().decode('utf-8'))
                        elif file_extension == '.pdf':
                            reader = PdfReader(file_handle)
                            uploaded_texts.append(
                                ''.join(page.extract_text() for page in reader.pages))
                        elif file_extension == '.docx':
                            doc = Document(file_handle)
                            uploaded_texts.append(
                                '\n'.join(p.text for p in doc.paragraphs))

                        file_handle.close()
                    except Exception as e:
                        messages.error(request, f"Error processing file {file.name}: {e}")
                        continue

                try:
                    json_output, external_reference = infer_quiz_json(
                        quiz_form, "\n".join(uploaded_texts))
                    save_quiz_from_json(json_output, external_reference, quiz)
                    return redirect('quiz', pk=quiz.id)

                except Exception as e:
                    messages.error(request, f"Error creating quiz: {e}")
                    return redirect('app')

            else:
                messages.error(request, "Invalid form submission.")

        return render(request, 'app.html', {'quiz_form': quiz_form, 'nickname': nickname})
    else:
        return redirect('login')


def profile(request):
    if request.user.is_authenticated:
        nickname = request.user.nickname

        if request.method == 'POST':
            form = ProfileForm(data=request.POST, instance=request.user)
            update = form.save(commit=False)
            update.user = request.user
            update.save()
        else:
            form = ProfileForm(instance=request.user)

        profile_info = {
            'nickname': nickname,
            'form': form,
        }

        return render(request, 'profile.html', profile_info)
    else:
        return redirect('login')


def bites(request):
    return render(request, 'bites.html')


def quizzes(request):
    if request.user.is_authenticated:
        quizzes = Quiz.objects.filter(
            user=request.user).order_by('-created_at')

        quiz_list = {
            'quizzes': quizzes,
        }
        return render(request, 'quizzes.html', quiz_list)
    else:
        return redirect('login')


def quiz(request, pk):
    if request.user.is_authenticated:
        quiz = get_object_or_404(Quiz, id=pk)
        questions = Question.objects.filter(quiz=quiz)
        choices = Choice.objects.filter(question__in=questions)
        explanations = Explanation.objects.filter(question__in=questions)
        reference = Reference.objects.get(quiz=quiz)

        total_questions = questions.count()
        total_explanations = explanations.count()
        correct_count = 0

        if request.method == 'POST':
            for question in questions:
                selected_choice_id = request.POST.get(
                    f'selected_choice_{question.id}')
                if selected_choice_id:
                    selected_choice = get_object_or_404(
                        Choice, pk=selected_choice_id)
                    if selected_choice.is_correct:
                        correct_count += 1

        quiz_data = {
            'quiz': quiz,
            'questions': questions,
            'choices': choices,
            'explanations': explanations,
            'total_explanations': total_explanations,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'reference': reference,
        }

        return render(request, 'quiz.html', quiz_data)
    else:
        return redirect('login')


def update_quiz(request, pk):
    if request.user.is_authenticated:
        selected_quiz = get_object_or_404(Quiz, id=pk)

        update_quiz_form = QuizForm(
            request.POST or None, instance=selected_quiz)
        update_question_formset = UpdateQuestionFormSet(
            request.POST or None, instance=selected_quiz)

        if request.method == 'POST':
            if update_quiz_form.is_valid() and update_question_formset.is_valid():
                update_quiz_form.save()
                questions = update_question_formset.save(commit=False)

                for question in questions:
                    question.quiz = selected_quiz
                    question.save()

                    # Update choices for the question
                    update_choice_formset = UpdateChoiceFormSet(
                        request.POST, instance=question)

                    if update_choice_formset.is_valid():
                        choices = update_choice_formset.save(commit=False)

                        for choice in choices:
                            choice.question = question
                            choice.save()

                messages.success(
                    request, "Quiz and choices have been updated!")
                return redirect('app')

        else:
            # Initialize the ChoiceFormSet for each question in the GET request
            for question_form in update_question_formset:
                question_form.update_choice_formset = UpdateChoiceFormSet(
                    instance=question_form.instance)

        # Prepare context to include a formset for each question's choices
        update_choice_formset = [UpdateChoiceFormSet(
            instance=question_form.instance) for question_form in update_question_formset]

        return render(request, 'update-quiz.html', {
            'update_quiz_form': update_quiz_form,
            'update_question_formset': update_question_formset,
            'update_choice_formset': update_choice_formset,
        })

    else:
        messages.warning(request, "You must be logged in to update quizzes.")
        return redirect('app')


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        useremail = request.POST['useremail']
        password = request.POST['password']

        user = authenticate(request, username=useremail, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have been successfully logged in!")
            return redirect("app")
        else:
            messages.warning(
                request, "There was an error login in, please try again...")
            return redirect("login")
    return render(request, 'login.html', {})


def logout_user(request):
    logout(request)
    messages.success(request, "You've been logged out...")
    return redirect("login")


def activate(request, uidb64, token):
    LearnerUser = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = LearnerUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, LearnerUser.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(
            request, 'Thank you for your email confirmation. Now you can login your account.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')

    return redirect('app')


def activateEmail(request, user, to_email):
    mail_subject = 'Activate your Knowmona account'
    message = render_to_string('template_activate_account.html', {
        'user': user.email,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request, f'Hi {user.nickname}! Please go to you email, {to_email}, inbox and click on \
            received activation link to confirm and complete the registration. Note: Check your spam folder.')
    else:
        messages.error(request, f'Problem sending confirmation email to {
                       to_email}, check if you typed it correctly.')


def signup_user(request):
    if request.method == 'POST':
        form = SignUpLearnerUser(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
            return redirect('signup')
    else:
        form = SignUpLearnerUser()
        return render(request, 'signup.html', {'form': form})

    return render(request, 'signup.html', {'form': form})


def delete_quiz(request, pk):
    if request.user.is_authenticated:
        selected_quiz = Quiz.objects.get(id=pk)
        selected_quiz.delete()
        messages.success(request, "The quiz has been deleted successfully...")
        return redirect('quizzes')
    else:
        return redirect('app')


# Google authentication logic


@csrf_exempt
def auth_receiver(request):
    """
    Google calls this URL after the user has signed in with their Google account.
    """
    print('Inside')
    token = request.POST['credential']
    print(token)

    user_data = id_token.verify_oauth2_token(
        token, requests.Request(), os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    )
    print(user_data)
    account_email = user_data["email"]
    account_given_name = user_data["given_name"]
    account_family_name = user_data["family_name"]
    user, created = LearnerUser.objects.get_or_create(
        email=account_email,
        first_name=account_given_name,
        last_name=account_family_name,
    )
    if user is not None:
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "You have been successfully logged in!")
        return redirect("app")
    else:
        messages.warning(
            request, "There was an error login in, please try again...")
        return redirect("login")


def sign_out(request):
    del request.session['user_data']
    return redirect('login')
