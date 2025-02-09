import json
import os
from django.http import JsonResponse
from docx import Document
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from google.oauth2 import id_token
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth import login
from django.core.mail import EmailMessage
from google.auth.transport import requests
from .tokens import account_activation_token
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from .utils import infer_quiz_json, save_quiz_from_json
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .forms import SignUpLearnerUser, QuizForm, UpdateQuestionFormSet, UpdateChoiceFormSet, ProfileForm, SetPasswordForm, PasswordResetForm
from .models import LearnerUser, Quiz, Question, Choice, Reference, Explanation, UploadedFile, UserEnergy, Suggestion

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
    if not request.user.is_authenticated:
        return redirect('login')

    nickname = getattr(request.user, 'nickname', None)
    user_energy = UserEnergy.objects.get_or_create(user=request.user)[0]
    user_energy.reset_if_new_day()  # Check and reset if it's a new day

    quiz_form = QuizForm(
        initial={'question_difficulty': 'Average', 'tone': 'Casual'})

    if request.method == 'POST':
        # Check energy before processing the form
        if not user_energy.use_energy(10):
            messages.error(request, "Sorry, requests are currently limited. You can create quizzes again tomorrow!")
            return redirect('app')

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
                    messages.error(request, f"Error processing file {
                                   file.name}: {e}")
                    continue

            try:
                json_output, external_reference = infer_quiz_json(
                    quiz_form, "\n".join(uploaded_texts))
                save_quiz_from_json(json_output, external_reference, quiz)
                return redirect('quiz', pk=quiz.id)
            except Exception as e:
                # Refund energy if quiz creation fails
                user_energy.energy += 10
                user_energy.save()
                messages.error(request, f"Error creating quiz: {e}")
                return redirect('app')
        else:
            messages.error(request, "Invalid form submission.")


    suggestions = Suggestion.objects.all()[:3]

    context = {
        'quiz_form': quiz_form,
        'nickname': nickname,
        'user_xp': request.user.experience_points,
        'user_energy': user_energy.energy,  # Add energy to context
        'suggestions': suggestions,
    }
    return render(request, 'app.html', context)


def profile(request):
    if request.user.is_authenticated:
        nickname = request.user.nickname
        email = request.user.email
        first_name = request.user.first_name
        last_name = request.user.last_name

        if request.method == 'POST':
            form = ProfileForm(data=request.POST, instance=request.user)
            update = form.save(commit=False)
            update.user = request.user
            update.save()
            messages.success(request, "Your profile has been updated!")
        else:
            form = ProfileForm(instance=request.user)

        profile_info = {
            'nickname': nickname,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'form': form,
        }

        return render(request, 'profile.html', profile_info)
    else:
        return redirect('login')


def quizzes(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    context = {
        'quizzes': Quiz.objects.filter(user=request.user).order_by('-created_at'),
        'shared_quizzes': Quiz.objects.filter(shared_with=request.user).order_by('-created_at')
    }
    return render(request, 'quizzes.html', context)

def shared_quizzes(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    context = {
        'shared_quizzes': Quiz.objects.filter(shared_with=request.user).order_by('-created_at')
    }
    return render(request, 'shared.html', context)
    
def share_with_all_friends(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    
    if request.method == 'POST':
        count = quiz.share_with_friends(request.user)
        if count > 0:
            messages.success(request, f"Shared with {count} friends!")
        else:
            messages.warning(request, "No friends to share with")
    
    return redirect('quizzes')


def unshare_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    
    if request.method == 'POST':
        # Remove all shared connections
        removed_count = quiz.shared_with.count()
        quiz.shared_with.clear()
        messages.success(request, f"Unshared from {removed_count} friends")
    
    return redirect('quizzes')

def unfriend(request, friend_id):
    friend = get_object_or_404(LearnerUser, id=friend_id)
    
    if request.method == 'POST':
        # Remove mutual friendship
        request.user.friends.remove(friend)
        friend.friends.remove(request.user)
        
        # Delete any pending friend requests
        FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=friend) |
            Q(from_user=friend, to_user=request.user)
        ).delete()
        
        messages.success(request, f"Unfriended {friend.nickname}")
    
    return redirect('friends')



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

        if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle XP updates via AJAX
            data = json.loads(request.body)
            xp_amount = data.get('xp_amount', 0)
            request.user.experience_points += xp_amount
            request.user.save()
            return JsonResponse({
                'status': 'success',
                'new_xp': request.user.experience_points,
                'xp_gained': xp_amount
            })

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


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from .models import LearnerUser, FriendRequest

@login_required
def friends(request):
    search_query = request.GET.get('query', None)
    user_list = LearnerUser.objects.none()  # Empty initial queryset

    if search_query:
        user_list = LearnerUser.objects.exclude(id=request.user.id).filter(
            Q(nickname__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    friends = request.user.friends.all()
    sent_requests = FriendRequest.objects.filter(from_user=request.user)
    received_requests = FriendRequest.objects.filter(to_user=request.user)

    context = {
        'user_list': user_list,
        'friends': friends,
        'sent_requests': sent_requests,
        'received_requests': received_requests,
        'search_query': search_query,
    }
    return render(request, 'friends.html', context)


@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(LearnerUser, id=user_id)
    
    # Prevent duplicate requests or existing friendships
    if request.user.friends.filter(id=to_user.id).exists():
        messages.warning(request, 'You are already friends!')
    elif FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
        messages.warning(request, 'Friend request already sent!')
    else:
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        messages.success(request, 'Friend request sent!')
    
    return redirect('friends')

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    request.user.friends.add(friend_request.from_user)
    friend_request.from_user.friends.add(request.user)
    friend_request.delete()
    messages.success(request, f'You are now friends with {friend_request.from_user.nickname}!')
    return redirect('friends')

@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.delete()
    messages.info(request, 'Friend request declined.')
    return redirect('friends')



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
        messages.error(request, f'Problem sending confirmation email to {to_email}, check if you typed it correctly.')


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
    
def delete_user(request):
    if request.user.is_authenticated:
        account = LearnerUser.objects.get(email=request.user.email)
        account.delete()
        messages.success(request, "Your account has been successfully deleted...")
        return redirect('login')
    else:
        return redirect('login')


# Google authentication logic


@csrf_exempt
def auth_receiver(request):
    token = request.POST['credential']
    user_data = id_token.verify_oauth2_token(
        token, requests.Request(), os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    )
    
    account_email = user_data["email"]
    account_given_name = user_data["given_name"]
    account_family_name = user_data["family_name"]

    # Get or create user based on email only
    user, created = LearnerUser.objects.get_or_create(
        email=account_email,
        defaults={
            'nickname': account_given_name,
            'first_name': account_given_name,
            'last_name': account_family_name,
        }
    )

    # Update user details if they already existed
    if not created:
        user.nickname = account_given_name
        user.first_name = account_given_name
        user.last_name = account_family_name
        user.save()

    if user is not None:
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "You have been successfully logged in!")
        return redirect("app")
    else:
        messages.warning(request, "There was an error logging in, please try again...")
        return redirect("login")



def sign_out(request):
    del request.session['user_data']
    return redirect('login')

@login_required
def password_change(request):
    user = request.user
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password has been changed")
            return redirect('login')
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

    form = SetPasswordForm(user)
    return render(request, 'password_reset_confirm.html', {'form': form})

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            associated_user = get_user_model().objects.filter(Q(email=user_email)).first()
            if associated_user:
                subject = "Password Reset request"
                message = render_to_string("template_reset_password.html", {
                    'user': associated_user,
                    'domain': get_current_site(request).domain,
                    'uid': urlsafe_base64_encode(force_bytes(associated_user.pk)),
                    'token': account_activation_token.make_token(associated_user),
                    "protocol": 'https' if request.is_secure() else 'http'
                })
                email = EmailMessage(subject, message, to=[associated_user.email])
                if email.send():
                    messages.success(request,
                        """
                        <h2>Password reset sent</h2><hr>
                        <p>
                            We've emailed you instructions for setting your password, if an account exists with the email you entered. 
                            You should receive them shortly.<br>If you don't receive an email, please make sure you've entered the address 
                            you registered with, and check your spam folder.
                        </p>
                        """
                    )
                else:
                    messages.error(request, "Problem sending reset password email, <b>SERVER PROBLEM</b>")

            return redirect('homepage')

        for key, error in list(form.errors.items()):
            if key == 'captcha' and error[0] == 'This field is required.':
                messages.error(request, "You must pass the reCAPTCHA test")
                continue

    form = PasswordResetForm()
    return render(
        request=request, 
        template_name="password_reset.html", 
        context={"form": form}
        )

def passwordResetConfirm(request, uidb64, token):
    User = LearnerUser
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been set. You may go ahead and <b>log in </b> now.")
                return redirect('homepage')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)

        form = SetPasswordForm(user)
        return render(request, 'password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, "Link is expired")

    messages.error(request, 'Something went wrong, redirecting back to Homepage')
    return redirect("homepage")
