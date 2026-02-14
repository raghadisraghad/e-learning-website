from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe
from embed_video.fields import EmbedVideoField
import os

def user_avatar_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/users/avatars/<filename>
    ext = os.path.splitext(filename)[1].lower()
    return f'users/avatars/user_{instance.id}{ext}'

def tutorial_thumbnail_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/tutorials/thumbnails/<filename>
    return f'tutorials/thumbnails/{filename}'

def notes_cover_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/notes/covers/<filename>
    return f'notes/covers/{filename}'

def notes_file_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/notes/files/<filename>
    return f'notes/files/{filename}'

class User(AbstractUser):
    first_name = models.CharField(max_length=255, default='')
    last_name = models.CharField(max_length=255, default='')
    phonenumber = models.CharField(max_length=255, blank=True, null=True)
    is_learner = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    avatar = models.ImageField(
        upload_to=user_avatar_path, 
        default='users/avatars/default_avatar.png',  # Updated default path
        blank=True
    )
    last_announcements_check = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # First save to generate ID if it's a new user
        if not self.pk:
            super().save(*args, **kwargs)
            # Update avatar path with user ID
            if self.avatar and 'default' not in self.avatar.name:
                self.avatar.name = f'users/avatars/user_{self.id}{os.path.splitext(self.avatar.name)[1]}'
            super().save(update_fields=['avatar'])
        else:
            super().save(*args, **kwargs)

class Announcement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    posted_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.content)

class Course(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default='#007bff')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    def get_html_badge(self):
        name = escape(self.name)
        color = escape(self.color)
        html = '<span class="badge badge-primary" style="background-color: %s">%s</span>' % (color, name)
        return mark_safe(html)
        
class Tutorial(models.Model):
    title = models.CharField(max_length=50)
    content = models.TextField()
    thumb = models.ImageField(
        upload_to=tutorial_thumbnail_path, 
        null=True, 
        blank=True
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = EmbedVideoField(blank=True, null=True)

    def delete(self, *args, **kwargs):
        # Delete thumbnail file when tutorial is deleted
        if self.thumb:
            self.thumb.delete()
        super().delete(*args, **kwargs)

class Notes(models.Model):
    title = models.CharField(max_length=500)
    file = models.FileField(
        upload_to=notes_file_path, 
        null=True, 
        blank=True
    )
    cover = models.ImageField(
        upload_to=notes_cover_path, 
        null=True, 
        blank=True
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        # Delete files when notes is deleted
        if self.file:
            self.file.delete()
        if self.cover:
            self.cover.delete()
        super().delete(*args, **kwargs)    

class Quiz(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField('Question', max_length=255)

    def __str__(self):
        return self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField('Answer', max_length=255)
    is_correct = models.BooleanField('Correct answer', default=False)

    def __str__(self):
        return self.text

class Learner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    quizzes = models.ManyToManyField(Quiz, through='TakenQuiz')
    interests = models.ManyToManyField(Course, related_name='interested_learners')

    def get_unanswered_questions(self, quiz):
        answered_questions = self.quiz_answers \
            .filter(answer__question__quiz=quiz) \
            .values_list('answer__question__pk', flat=True)
        questions = quiz.questions.exclude(pk__in=answered_questions).order_by('text')
        return questions

    def __str__(self):
        return self.user.username

class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    interest = models.ManyToManyField(Course, related_name="more_locations")

class TakenQuiz(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='taken_quizzes')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='taken_quizzes')
    score = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)

class LearnerAnswer(models.Model):
    student = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='quiz_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='+')