from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.forms import inlineformset_factory
from .models import Quiz, Question, Choice, LearnerUser

class QuizForm(forms.ModelForm):

	QUESTION_DIFFICULTY_CHOICES	= {
		"easy": "Easy",
		"average": "Average",
		"hard": "Hard",
	}
	TONE_CHOICES = {
		"casual": "Casual",
		"professional": "Professional",
		"academic": "Academic",
	}

	topic = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Enter any topic", "class":"form-control"}), label="")
	question_difficulty = forms.ChoiceField(choices=QUESTION_DIFFICULTY_CHOICES, widget=forms.RadioSelect(), initial={'average': 'Average'})
	tone = forms.ChoiceField(choices=TONE_CHOICES, widget=forms.RadioSelect(), initial={'casual': 'Casual'})
	
	class Meta:
		model = Quiz
		fields = ('topic', 'question_difficulty', 'tone')
		exclude = ("user",)

	def __init__(self, *args, **kwargs):
		super(QuizForm, self).__init__(*args, **kwargs)
		self.fields['question_difficulty'].required = False
		self.fields['tone'].required = False

class CreateQuestion(forms.ModelForm):
	text = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Enter a question", "class":"form-control"}), label="")

	class Meta:
		model = Question
		fields = ('text',)
		exclude = ("user",)

class CreateChoice(forms.ModelForm):
	text = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Enter a choice", "class":"form-control"}), label="")
	is_correct = forms.CheckboxInput(attrs={'class': 'form-check' "type"})
	class Meta:
		model = Choice
		fields = ('text','is_correct',)
		exclude = ("user",)

QuestionFormSet = inlineformset_factory(Quiz, Question, form=CreateQuestion, extra=10)
ChoiceFormSet = inlineformset_factory(Question, Choice, form=CreateChoice, extra=4)

UpdateQuestionFormSet = inlineformset_factory(Quiz, Question, form=CreateQuestion, extra=0)
UpdateChoiceFormSet = inlineformset_factory(Question, Choice, form=CreateChoice, extra=0)

class SignUpLearnerUser(UserCreationForm):

	class Meta:
		model = LearnerUser
		fields = ('email', 'nickname', 'password1', 'password2')

	email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control rounded-pill', 'placeholder':'Email'}))

	def __init__(self, *args, **kwargs):
		super(SignUpLearnerUser, self).__init__(*args, **kwargs)

		self.fields['nickname'].widget.attrs['class'] = 'form-control rounded-pill'
		self.fields['nickname'].widget.attrs['placeholder'] = 'Nickname (optional)'
		self.fields['nickname'].label = ''

		self.fields['password1'].widget.attrs['class'] = 'form-control rounded-pill'
		self.fields['password1'].widget.attrs['placeholder'] = 'Password'
		self.fields['password1'].label = ''
		self.fields['password1'].help_text = ''

		self.fields['password2'].widget.attrs['class'] = 'form-control rounded-pill'
		self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'
		self.fields['password2'].label = ''
		self.fields['password2'].help_text = '<p class="form-text text-muted small">Enter the same password as before, for verification.<p>'


	def clean_email(self):
			email = self.cleaned_data.get('email')
			if LearnerUser.objects.filter(email=email).exists():
				raise forms.ValidationError("Sorry, an account with this email already exists.")
			return email
	
class ProfileForm(forms.ModelForm):
	email = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Email", "class":"form-control"}), label="")
	nickname = forms.CharField(widget=forms.widgets.TextInput(attrs={"placeholder":"Nickname", "class":"form-control"}), label="")
	first_name = forms.CharField(widget=forms.widgets.TextInput(attrs={"placeholder":"First name", "class":"form-control"}), label="")
	last_name = forms.CharField(widget=forms.widgets.TextInput(attrs={"placeholder":"Last name", "class":"form-control"}), label="")
	class Meta:
		model = LearnerUser
		fields = ('email', 'nickname')
