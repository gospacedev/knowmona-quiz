from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class MainUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class LearnerUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=50, blank=True, unique=False)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    experience_points = models.IntegerField(default=0)
    friends = models.ManyToManyField("LearnerUser", blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = MainUserManager()

    def __str__(self):
        return self.email


class FriendRequest(models.Model):
    from_user = models.ForeignKey(
        LearnerUser, related_name="from_user", on_delete=models.CASCADE)
    to_user = models.ForeignKey(
        LearnerUser, related_name="to_user", on_delete=models.CASCADE)

    def __str__(self):
        return (f"From {self.from_user} to {self.to_user}")


class UserEnergy(models.Model):
    user = models.OneToOneField(LearnerUser, on_delete=models.CASCADE)
    energy = models.IntegerField(default=100)
    last_reset = models.DateTimeField(default=timezone.now)

    def reset_if_new_day(self):
        now = timezone.now()
        if now.date() > self.last_reset.date():
            self.energy = 100
            self.last_reset = now
            self.save()

    def use_energy(self, amount=10):
        self.reset_if_new_day()
        if self.energy >= amount:
            self.energy -= amount
            self.save()
            return True
        return False

    def __str__(self):
        return (f"{self.user}")


class Quiz(models.Model):
    QUESTION_DIFFICULTY_CHOICES = {
        "easy": "Easy",
        "average": "Average",
        "hard": "Hard",
    }
    TONE_CHOICES = {
        "casual": "Casual",
        "professional": "Professional",
        "academic": "Academic",
    }

    topic = models.CharField(max_length=1000)
    question_difficulty = models.CharField(
        max_length=12, choices=QUESTION_DIFFICULTY_CHOICES, default="average")
    tone = models.CharField(
        max_length=12, choices=TONE_CHOICES, default="casual")

    user = models.ForeignKey(LearnerUser, on_delete=models.CASCADE, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f"{self.topic}")


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField(max_length=1000)

    def __str__(self):
        return (f"{self.text}")


class Explanation(models.Model):
    question = models.ForeignKey(
        Question, related_name='explanation', on_delete=models.CASCADE)
    text = models.CharField(max_length=1000)

    def __str__(self):
        return (f"{self.text}")


class Choice(models.Model):
    question = models.ForeignKey(
        Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=1000)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return (f"{self.text}")


class Reference(models.Model):
    quiz = models.ForeignKey(
        Quiz, related_name='reference', on_delete=models.CASCADE)
    text = models.CharField(max_length=5000)

    def __str__(self):
        return (f"{self.text}")


class UploadedFile(models.Model):
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="uploaded_files")
    file = models.FileField(upload_to='uploaded_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} (uploaded by {self.user.username})"
