from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView 
from django.views.generic.edit import UpdateView
from django.http import JsonResponse
from ..forms import CustomUserChangeForm, TakeQuizForm, LearnerInterestsForm
from django.utils import timezone
from django.db.models import Count
from ..models import TakenQuiz, Quiz, Learner, Notes, Announcement,Tutorial
from django.db import transaction
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.csrf import csrf_exempt
from django.views import View

def home_learner(request):
    if not request.user.is_learner:
        return redirect('home')
    return render(request, 'dashboard/learner/home.html')

def LearnerProfile(request):
    if not request.user.is_learner:
        return redirect('home')
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('learnerprofile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'dashboard/learner/user_profile.html', {'form': form})

def LearnerUpdatePassword(request):
    if not request.user.is_learner:
        return redirect('home')
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('learnerprofile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'user_profile.html', {'form': form})

class LearnerAllAnnonce(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'dashboard/learner/tise_list.html'

    def get_queryset(self):
        return Announcement.objects.filter(posted_at__lt=timezone.now()).order_by('-posted_at')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_learner:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
@csrf_exempt
def ClearNotification(request):
    if not request.user.is_learner:
        return redirect('home')
    user = request.user
    user.profile.new_announcements_count = 0
    user.profile.save()
    return JsonResponse({'status': 'success'})

class Notification(View):
    def get(self, request, *args, **kwargs):
        last_check_time = request.user.last_announcements_check
        
        new_announcements = Announcement.objects.filter(posted_at__gt=last_check_time)
        
        request.user.last_announcements_check = timezone.now()
        request.user.save()
        
        data = {
            'count': new_announcements.count(),
            'announcements': list(new_announcements.values('user', 'content', 'posted_at'))
        }
        return JsonResponse(data)
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_learner:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
class LNotesList(ListView):
    model = Notes
    template_name = 'dashboard/learner/list_notes.html'
    context_object_name = 'notes'
    paginate_by = 4

    def get_queryset(self):
        return Notes.objects.order_by('-id')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_learner:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
def ltutorial(request):
    if not request.user.is_learner:
        return redirect('home')
    tutorials = Tutorial.objects.all().order_by('-created_at')
    tutorials = {'tutorials':tutorials}
    return render(request, 'dashboard/learner/list_tutorial.html', tutorials)

class LTutorialDetail(LoginRequiredMixin, DetailView):
    model = Tutorial
    template_name = 'dashboard/learner/tutorial_detail.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_learner:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class LearnerInterestsView(UpdateView):
    model = Learner
    form_class = LearnerInterestsForm
    template_name = 'dashboard/learner/interests_form.html'
    success_url = reverse_lazy('lquiz_list')

    def get_object(self):
        return self.request.user.learner

    def form_valid(self, form):
        messages.success(self.request, 'Course Was Updated Successfully')
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_learner:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class LQuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'dashboard/learner/quiz_list.html'

    def get_queryset(self):
        learner = self.request.user.learner
        learner_interests = learner.interests.values_list('pk', flat=True)
        taken_quizzes = learner.quizzes.values_list('pk', flat=True)
        queryset = Quiz.objects.filter(course__in=learner_interests) \
            .exclude(pk__in=taken_quizzes) \
            .annotate(questions_count=Count('questions')) \
            .filter(questions_count__gt=0)
        return queryset     
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_learner:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    template_name = 'dashboard/learner/taken_quiz_list.html'

    def get_queryset(self):
        queryset = self.request.user.learner.taken_quizzes \
            .select_related('quiz', 'quiz__course') \
            .order_by('quiz__name')
        return queryset
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_learner:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
def take_quiz(request, pk):
    if not request.user.is_learner:
        return redirect('home')
    quiz = get_object_or_404(Quiz, pk=pk)
    learner = request.user.learner

    if learner.quizzes.filter(pk=pk).exists():
        return render(request, 'dashboard/learner/taken_quiz.html')

    total_questions = quiz.questions.count()
    unanswered_questions = learner.get_unanswered_questions(quiz)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeQuizForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                learner_answer = form.save(commit=False)
                learner_answer.student = learner
                learner_answer.save()
                if learner.get_unanswered_questions(quiz).exists():
                    return redirect('take_quiz', pk)
                else:
                    correct_answers = learner.quiz_answers.filter(answer__question__quiz=quiz, answer__is_correct=True).count()
                    score = round((correct_answers / total_questions) * 100.0, 2)
                    TakenQuiz.objects.create(learner=learner, quiz=quiz, score=score)
                    if score < 50.0:
                        messages.warning(request, 'Better luck next time! Your score for the quiz %s was %s.' % (quiz.name, score))
                    else:
                        messages.success(request, 'Congratulations! You completed the quiz %s with success! You scored %s points.' % (quiz.name, score))
                    return redirect('lquiz_list')
    else:
        form = TakeQuizForm(question=question)

    return render(request, 'dashboard/learner/take_quiz_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress
    })        