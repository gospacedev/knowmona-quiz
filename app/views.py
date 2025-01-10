from django.shortcuts import render
from google.auth.transport import requests
from google.oauth2 import id_token
from django.views.decorators.csrf import csrf_exempt
import os
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import LearnerUser, Quiz, Question, Choice, Reference, Explanation
from .forms import SignUpLearnerUser, QuizForm, UpdateQuestionFormSet, UpdateChoiceFormSet, ProfileForm
from .utils import infer_quiz_json, save_quiz_from_json
from django.contrib.auth import login
from django.shortcuts import render, redirect


def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def contact(request):
    return render(request, "contact.html")


def app(request):
    nickname = None

    if request.user.is_authenticated:
        nickname = request.user.nickname

        if request.method == 'POST':
            quiz_form = QuizForm(request.POST, initial={
                                 'question_difficulty': 'Average', 'tone': 'Casual'})
            if quiz_form.is_valid():
                quiz = quiz_form.save(commit=False)
                json_output, external_reference = infer_quiz_json(quiz_form)
                try:
                    quiz.save()
                    save_quiz_from_json(json_output, external_reference, quiz)
                    new_quiz_id = quiz.id
                    return redirect('quiz_record', pk=new_quiz_id)  # Not yet

                except Exception as e:
                    messages.error(request, f"Error creating quiz: {e}")
            else:
                messages.error(
                    request, "There was an error with your form submission.")
        else:
            quiz_form = QuizForm()

        app_data = {
            'quiz_form': quiz_form,
            'nickname': nickname,
        }

        return render(request, 'app.html', app_data)
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
    quizzes = Quiz.objects.all()

    if request.user.is_authenticated:

        quiz_list = {
            'quizzes': quizzes,
        }
        return render(request, 'quizzes.html', quiz_list)
    else:
        return redirect('login')


def quiz_record(request, pk):
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


def signup_user(request):
    if request.method == 'POST':
        form = SignUpLearnerUser(request.POST)
        if form.is_valid():
            user = form.save()            
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']

            user = authenticate(username=email, password=password)
            messages.success(
                request, "You Have Successfully Registered! Welcome!")
            return redirect('app')
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
        token, requests.Request(), os.environ['GOOGLE_OAUTH_CLIENT_ID']
    )
    print(user_data)
    account_email = user_data["email"]
    account_given_name = user_data["given_name"]
    user, created = LearnerUser.objects.get_or_create(
        email=account_email,
        nickname=account_given_name,
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
