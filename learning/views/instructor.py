from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView 
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from ..forms import CustomUserChangeForm, QuestionForm, BaseAnswerInlineFormSet, TutorialForm, PostForm
from django.urls import reverse
from django.utils import timezone
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from ..models import Answer, Quiz, Question, Course, Notes, Announcement,Tutorial, User, TakenQuiz
from django.db import transaction
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.csrf import csrf_exempt
from django.views import View

def home_instructor(request):
    if not request.user.is_instructor:
        return redirect('home')

    # Get current instructor
    instructor = request.user
    
    # Total students (all learners)
    total_students = User.objects.filter(is_learner=True).count()
    
    # Total courses (all courses in the system)
    total_courses = Course.objects.count()
    
    # Total quizzes created by this instructor
    total_quizzes = Quiz.objects.filter(owner=instructor).count()
    
    # Calculate average score for this instructor's quizzes
    avg_score = TakenQuiz.objects.filter(
        quiz__owner=instructor
    ).aggregate(Avg('score'))['score__avg'] or 0
    
    # Calculate student growth (new students in last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    new_students = User.objects.filter(
        is_learner=True, 
        date_joined__gte=thirty_days_ago
    ).count()
    student_growth = round((new_students / total_students * 100) if total_students > 0 else 0, 1)
    
    # Calculate course growth (new courses that have quizzes by this instructor in last 30 days)
    new_courses = Course.objects.filter(
        quizzes__owner=instructor,
        quizzes__id__isnull=False
    ).distinct().count()
    # Since we don't have created_at on Course, we'll use a different metric
    course_growth = round((new_courses / total_courses * 100) if total_courses > 0 else 0, 1)
    
    # Calculate quiz growth (new quizzes in last 30 days - using auto_now_add)
    # Note: Quiz model doesn't have created_at, so we'll estimate based on ID
    # Alternative: You could add created_at field to Quiz model
    total_quizzes_count = Quiz.objects.filter(owner=instructor).count()
    recent_quizzes_count = Quiz.objects.filter(
        owner=instructor
    ).order_by('-id')[:10].count()  # Last 10 quizzes as proxy for "recent"
    quiz_growth = round((recent_quizzes_count / total_quizzes_count * 100) if total_quizzes_count > 0 else 0, 1)
    
    # Calculate score trend (compare recent quizzes to older ones)
    # Get all taken quizzes for this instructor, ordered by date
    all_taken = TakenQuiz.objects.filter(
        quiz__owner=instructor
    ).select_related('quiz').order_by('-date')
    
    recent_taken = all_taken[:20]  # Last 20 attempts
    older_taken = all_taken[20:40]  # Next 20 attempts
    
    recent_avg = recent_taken.aggregate(Avg('score'))['score__avg'] or 0
    older_avg = older_taken.aggregate(Avg('score'))['score__avg'] or 0
    
    if older_avg > 0:
        score_trend = round(((recent_avg - older_avg) / older_avg * 100), 1)
    else:
        score_trend = 0
    
    # Get recent activities (last 10)
    recent_activities = []
    
    # Recent quiz completions (using date field which exists)
    recent_taken_quizzes = TakenQuiz.objects.filter(
        quiz__owner=instructor
    ).select_related('quiz', 'learner__user').order_by('-date')[:5]
    
    for taken in recent_taken_quizzes:
        time_diff = timezone.now() - taken.date
        if time_diff.days > 0:
            time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds // 3600 > 0:
            hours = time_diff.seconds // 3600
            time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = time_diff.seconds // 60
            time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            
        recent_activities.append({
            'type': 'success',
            'icon': 'check-circle',
            'title': f'Quiz "{taken.quiz.name}" completed by {taken.learner.user.username}',
            'time': time_str,
            'status': 'success',
            'score': f"{taken.score}%"
        })
    
    # Recent quiz creations (using ID as proxy for creation order)
    recent_quizzes = Quiz.objects.filter(
        owner=instructor
    ).order_by('-id')[:3]
    
    for quiz in recent_quizzes:
        # Since we don't have created_at, we'll use a generic "recently"
        recent_activities.append({
            'type': 'primary',
            'icon': 'plus-circle',
            'title': f'New quiz "{quiz.name}" created',
            'time': 'Recently',
            'status': 'primary'
        })
    
    # Recent tutorial uploads (using created_at which exists)
    recent_tutorials = Tutorial.objects.filter(
        user=instructor
    ).order_by('-created_at')[:3]
    
    for tutorial in recent_tutorials:
        time_diff = timezone.now() - tutorial.created_at
        if time_diff.days > 0:
            time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds // 3600 > 0:
            hours = time_diff.seconds // 3600
            time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = time_diff.seconds // 60
            time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            
        recent_activities.append({
            'type': 'info',
            'icon': 'video',
            'title': f'New tutorial "{tutorial.title}" uploaded',
            'time': time_str,
            'status': 'info'
        })
    
    # Recent notes uploads (Note: Notes model doesn't have timestamp)
    recent_notes = Notes.objects.filter(
        user=instructor
    ).order_by('-id')[:3]  # Using ID as proxy for creation order
    
    for notes in recent_notes:
        recent_activities.append({
            'type': 'warning',
            'icon': 'file-alt',
            'title': f'New notes "{notes.title}" uploaded',
            'time': 'Recently',
            'status': 'warning'
        })
    
    # Sort activities - we'll keep the ones with actual times first
    # This is a simple sort - you might want to enhance this
    recent_activities = recent_activities[:10]
    
    # Get counts for different statuses
    total_quiz_attempts = TakenQuiz.objects.filter(quiz__owner=instructor).count()
    
    # Quizzes that have been taken at least once
    quizzes_with_attempts = Quiz.objects.filter(
        owner=instructor,
        taken_quizzes__isnull=False
    ).distinct().count()
    
    # Get recent announcements (using posted_at which exists)
    recent_announcements = Announcement.objects.filter(
        user=instructor
    ).order_by('-posted_at')[:3]
    
    # Format announcements for display
    formatted_announcements = []
    for ann in recent_announcements:
        time_diff = timezone.now() - ann.posted_at
        if time_diff.days > 0:
            time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds // 3600 > 0:
            hours = time_diff.seconds // 3600
            time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = max(1, time_diff.seconds // 60)
            time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            
        formatted_announcements.append({
            'content': ann.content[:50] + '...' if len(ann.content) > 50 else ann.content,
            'time': time_str
        })
    
    # Get course distribution for the instructor
    courses_with_quizzes = Course.objects.filter(
        quizzes__owner=instructor
    ).annotate(
        quiz_count=Count('quizzes'),
        total_attempts=Count('quizzes__taken_quizzes')
    ).distinct()
    
    # Get performance by course
    course_performance = []
    for course in courses_with_quizzes:
        course_avg = TakenQuiz.objects.filter(
            quiz__course=course,
            quiz__owner=instructor
        ).aggregate(Avg('score'))['score__avg'] or 0
        course_performance.append({
            'name': course.name,
            'avg_score': round(course_avg, 1),
            'quiz_count': course.quiz_count,
            'total_attempts': course.total_attempts,
            'color': course.color
        })
    
    # Get top performing students
    top_students = Learner.objects.filter(
        taken_quizzes__quiz__owner=instructor
    ).annotate(
        avg_score=Avg('taken_quizzes__score'),
        quizzes_taken=Count('taken_quizzes')
    ).filter(quizzes_taken__gt=0).order_by('-avg_score')[:5]
    
    formatted_top_students = []
    for student in top_students:
        formatted_top_students.append({
            'name': student.user.get_full_name() or student.user.username,
            'username': student.user.username,
            'avg_score': round(student.avg_score, 1) if student.avg_score else 0,
            'quizzes_taken': student.quizzes_taken,
            'avatar': student.user.avatar.url if student.user.avatar else None
        })
    
    # Create context dictionary with ALL real data
    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_quizzes': total_quizzes,
        'avg_score': round(avg_score, 1),
        'student_growth': student_growth,
        'course_growth': course_growth,
        'quiz_growth': quiz_growth,
        'score_trend': score_trend,
        'recent_activities': recent_activities,
        'current_date': timezone.now(),
        'total_quiz_attempts': total_quiz_attempts,
        'quizzes_with_attempts': quizzes_with_attempts,
        'recent_announcements': formatted_announcements,
        'instructor_name': instructor.get_full_name() or instructor.username,
        'instructor_first_name': instructor.first_name or instructor.username,
        'instructor_email': instructor.email,
        'instructor_phone': instructor.phonenumber,
        'member_since': instructor.date_joined,
        'instructor_avatar': instructor.avatar.url if instructor.avatar else None,
        'course_performance': course_performance[:5],  # Top 5 courses
        'top_students': formatted_top_students,
        'total_courses_taught': courses_with_quizzes.count(),
    }

    return render(request, 'dashboard/instructor/home.html', context)
    
class InstructorAllAnnonce(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'dashboard/instructor/tise_list.html'

    def get_queryset(self):
        return Announcement.objects.filter(posted_at__lt=timezone.now()).order_by('-posted_at')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
class InstructorCreateAnnonce(CreateView):
    model = Announcement
    form_class = PostForm
    template_name = 'dashboard/instructor/post_form.html'
    success_url = reverse_lazy('instructorallannonce')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class QuizCreateView(CreateView):
    model = Quiz
    fields = ('name', 'course')
    template_name = 'dashboard/Instructor/quiz_add_form.html'

    def form_valid(self, form):
        quiz = form.save(commit=False)
        quiz.owner = self.request.user
        quiz.save()
        return redirect('quiz_change', quiz.pk)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class QuizUpateView(UpdateView):
    model = Quiz
    fields = ('name', 'course')
    template_name = 'dashboard/instructor/quiz_change_form.html'

    def get_context_data(self, **kwargs):
        kwargs['questions'] = self.get_object().questions.annotate(answers_count=Count('answers'))
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.quizzes.all()

    def get_success_url(self):
        return reverse('quiz_change', kwargs={'pk', self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
        
# def question_add(request, pk):
#     if not request.user.is_instructor:
#         return redirect('home')
#     quiz = get_object_or_404(Quiz, pk=pk, owner=request.user)

#     if request.method == 'POST':
#         form = QuestionForm(request.POST)
#         if form.is_valid():
#             question = form.save(commit=False)
#             question.quiz = quiz
#             question.save()
#             messages.success(request, 'You may now add answers/options to the question.')
#             return redirect('question_change', quiz.pk, question.pk)
#     else:
#         form = QuestionForm()

#     return render(request, 'dashboard/instructor/question_add_form.html', {'quiz': quiz, 'form': form})

def question_change(request, quiz_pk, question_pk):
    if not request.user.is_instructor:
        return redirect('home')
    quiz = get_object_or_404(Quiz, pk=quiz_pk, owner=request.user)
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)

    AnswerFormatSet = inlineformset_factory (
        Question,
        Answer,
        formset = BaseAnswerInlineFormSet,
        fields = ('text', 'is_correct'),
        min_num = 2,
        validate_min = True,
        max_num = 10,
        validate_max = True
        )

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = AnswerFormatSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                formset.save()
                formset.save()
            messages.success(request, 'Question And Answers Saved Successfully')
            return redirect('quiz_change', quiz.pk)
    else:
        form = QuestionForm(instance=question)
        formset = AnswerFormatSet(instance=question)
    return render(request, 'dashboard/instructor/question_change_form.html', {
        'quiz':quiz,
        'question':question,
        'form':form,
        'formset':formset
        })        

class QuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'dashboard/instructor/quiz_change_list.html'

    def get_queryset(self):
        queryset = self.request.user.quizzes \
        .select_related('course') \
        .annotate(questions_count = Count('questions', distinct=True)) \
        .annotate(taken_count = Count('taken_quizzes', distinct=True))
        return queryset    
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class QuestionDeleteView(DeleteView):
    model = Question
    context_object_name = 'question'
    template_name = 'dashboard/instructor/question_delete_confirm.html'
    pk_url_kwarg = 'question_pk'

    def get_context_data(self, **kwargs):
        question = self.get_object()
        kwargs['quiz'] = question.quiz
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        question = self.get_object()
        messages.success(request, 'The Question Was Deleted Successfully')
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Question.objects.filter(quiz__owner=self.request.user)

    def get_success_url(self):
        question = self.get_object()
        return reverse('quiz_change', kwargs={'pk': question.quiz_id})    
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class QuizResultsView(DeleteView):
    model = Quiz
    context_object_name = 'quiz'
    template_name = 'dashboard/instructor/quiz_results.html'

    def get_context_data(self, **kwargs):
        quiz = self.get_object()
        taken_quizzes =quiz.taken_quizzes.select_related('learner__user').order_by('-date')
        total_taken_quizzes = taken_quizzes.count()
        quiz_score = quiz.taken_quizzes.aggregate(average_score=Avg('score'))
        extra_context = {
        'taken_quizzes': taken_quizzes,
        'total_taken_quizzes': total_taken_quizzes,
        'quiz_score':quiz_score
        }

        kwargs.update(extra_context)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.quizzes.all()    
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class QuizDeleteView(DeleteView):
    model = Quiz
    context_object_name = 'quiz'
    template_name = 'dashboard/instructor/quiz_delete_confirm.html'
    success_url = reverse_lazy('quiz_change_list')

    def delete(self, request, *args, **kwargs):
        quiz = self.get_object()
        messages.success(request, 'The quiz %s was deleted with success!' % quiz.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.quizzes.all()
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

def question_add(request, pk):
    if not request.user.is_instructor:
        return redirect('home')
    quiz = get_object_or_404(Quiz, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'You may now add answers/options to the question.')
            return redirect('question_change', quiz.pk, question.pk)
    else:
        form = QuestionForm()

    return render(request, 'dashboard/instructor/question_add_form.html', {'quiz': quiz, 'form': form})

class QuizUpdateView(UpdateView):
    model = Quiz
    fields = ('name', 'course', )
    context_object_name = 'quiz'
    template_name = 'dashboard/instructor/quiz_change_form.html'

    def get_context_data(self, **kwargs):
        kwargs['questions'] = self.get_object().questions.annotate(answers_count=Count('answers'))
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing quizzes that belongs
        to the logged in user.
        '''
        return self.request.user.quizzes.all()

    def get_success_url(self):
        return reverse('quiz_change', kwargs={'pk': self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class CreatePost(CreateView):
    form_class = PostForm
    model = Announcement
    template_name = 'dashboard/instructor/post_form.html'
    success_url = reverse_lazy('llchat')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class TiseList(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'dashboard/instructor/tise_list.html'

    def get_queryset(self):
        return Announcement.objects.filter(posted_at__lt=timezone.now()).order_by('posted_at')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

def tutorial(request):
    if not request.user.is_instructor:
        return redirect('home')
    
    if request.method == 'POST':
        form = TutorialForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            return redirect('tutorial')
    else:
        form = TutorialForm()
    
    tutorials = Tutorial.objects.all()
    courses = Course.objects.only('id', 'name')
    context = {
        'courses': courses,
        'form': form,
        'tutorials': tutorials,
    }
    return render(request, 'dashboard/instructor/tutorial.html', context)

def deleteTutorial(request, tutorial_id):
    if not request.user.is_instructor:
        return redirect('home')

    try:
        tutorial = Tutorial.objects.get(id=tutorial_id)
        tutorial.delete()
    except Tutorial.DoesNotExist:
        pass

    return redirect('tutorial')

def publish_tutorial(request):
    if not request.user.is_instructor:
        return redirect('home')
    if request.method == 'POST':
        title = request.POST['title']
        course_id = request.POST['course_id']
        content = request.POST['content']
        thumb = request.FILES['thumb']
        current_user = request.user
        author_id = current_user.id
        print(author_id)
        print(course_id)
        a = Tutorial(title=title, content=content, thumb=thumb, user_id=author_id, course_id=course_id)
        a.save()
        messages.success(request, 'Tutorial was published successfully!')
        return redirect('tutorial')
    else:
        messages.error(request, 'Tutorial was not published successfully!')
        return redirect('tutorial')

def itutorial(request):
    if not request.user.is_instructor:
        return redirect('home')
    tutorials = Tutorial.objects.all().order_by('-created_at')
    tutorials = {'tutorials':tutorials}
    return render(request, 'dashboard/instructor/list_tutorial.html', tutorials)

class ITutorialDetail(LoginRequiredMixin, DetailView):
    model = Tutorial
    template_name = 'dashboard/instructor/tutorial_detail.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class LNotesList(ListView):
    model = Notes
    template_name = 'dashboard/instructor/list_notes.html'
    context_object_name = 'notes'
    paginate_by = 4

    def get_queryset(self):
        return Notes.objects.order_by('-id')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_instructor:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

def iadd_notes(request):
    if not request.user.is_instructor:
        return redirect('home')
    courses = Course.objects.only('id', 'name')
    context = {'courses':courses}
    return render(request, 'dashboard/instructor/add_notes.html', context)

def publish_notes(request):
    if not request.user.is_instructor:
        return redirect('home')
    if request.method == 'POST':
        title = request.POST['title']
        course_id = request.POST['course_id']
        cover = request.FILES['cover']
        file = request.FILES['file']
        current_user = request.user
        user_id = current_user.id

        a = Notes(title=title, cover=cover, file=file, user_id=user_id, course_id=course_id)
        a.save()
        messages.success = (request, 'Notes Was Published Successfully')
        return redirect('lnotes')
    else:
        messages.error = (request, 'Notes Was Not Published Successfully')
        return redirect('iadd_notes')

def update_file(request, pk):
    if not request.user.is_instructor:
        return redirect('home')
    if request.method == 'POST':
        file = request.FILES['file']
        file_name = request.FILES['file'].name

        fs = FileSystemStorage()
        file = fs.save(file.name, file)
        fileurl = fs.url(file)
        file = file_name
        print(file)

        Notes.objects.filter(id = pk).update(file = file)
        messages.success = (request, 'Notes was updated successfully!')
        return redirect('lnotes')
    else:
        return render(request, 'dashboard/instructor/update.html')

def InstructorProfile(request):
    if not request.user.is_instructor:
        return redirect('home')
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('instructorprofile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'dashboard/instructor/user_profile.html', {'form': form})

def UpdatePassword(request):
    if not request.user.is_instructor:
        return redirect('home')
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('instructorprofile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'user_profile.html', {'form': form})
    
@csrf_exempt
def ClearNotification(request):
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