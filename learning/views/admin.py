from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views.generic.edit import CreateView
from ..forms import CustomUserChangeForm, LearnerSignUpForm, InstructorSignUpForm, PostForm
from ..models import User,Course,Announcement
from django.views.generic import ListView 
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.csrf import csrf_exempt
from django.views import View

def dashboard(request):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('home')
    return render(request, 'dashboard/admin/home.html')

def course(request):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST['name']
        color = request.POST['color']

        a = Course(name=name, color=color)
        a.save()
        messages.success(request, 'New Course Was Registered Successfully')
        return redirect('course')
    else:
        courses = Course.objects.all()
        return render(request, 'dashboard/admin/course.html', {'courses': courses})

def DeleteCourse(request, course_id):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.success(request, 'Course was deleted successfully')
    return redirect('course')

class InstructorSignUpView(CreateView):
    model = User
    form_class = InstructorSignUpForm
    template_name = 'dashboard/admin/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'instructor'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, 'Instructor Was Added Successfully')
        return redirect('addinstructor')

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_superuser):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class AdminLearner(CreateView):
    model = User
    form_class = LearnerSignUpForm
    template_name = 'dashboard/admin/learner_signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'learner'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, 'Learner Was Added Successfully')
        return redirect('addlearner')
    
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_superuser):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
class ListUserView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'dashboard/admin/list_users.html'
    context_object_name = 'users'
    paginated_by = 10


    def get_queryset(self):
        return User.objects.order_by('-id')

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_superuser):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
class AdminDeleteAnnonce(SuccessMessageMixin, DeleteView):
    model = Announcement
    template_name = 'dashboard/admin/tise_list.html'
    success_url = reverse_lazy('allannonce')
    success_message = "Announcement Was Deleted Successfully"

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_superuser):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
   
class AdminAllAnnonce(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'dashboard/admin/tise_list.html'

    def get_queryset(self):
        return Announcement.objects.filter(posted_at__lt=timezone.now()).order_by('-posted_at')

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_superuser):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
class AdminCreateAnnonce(CreateView):
    model = Announcement
    form_class = PostForm
    template_name = 'dashboard/admin/post_form.html'
    success_url = reverse_lazy('allannonce')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_superuser):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
class AdminDeleteUser(SuccessMessageMixin, DeleteView):
    model = User
    template_name = 'dashboard/admin/list_users.html'
    success_url = reverse_lazy('allusers')
    success_message = "User Was Deleted Successfully"

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_superuser):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

def AdminProfile(request):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('home')
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('adminprofile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'dashboard/admin/user_profile.html', {'form': form})

def promote_to_admin(request):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('home')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = User.objects.get(id=user_id)
        user.is_admin = True
        user.save()
        messages.success(request, f"{user.username} has been promoted to admin.")
        return redirect('allusers')
    
def remove_admin(request):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('home')
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            user = User.objects.get(id=user_id)
            user.is_admin = False
            user.save()
            messages.success(request, f"{user.username} has been removed as an admin.")
            return redirect('allusers')
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return redirect('allusers')

def create_user_form(request):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('home')
    users = User.objects.all()
    
    context = {
        'users': users
    }
    
    return render(request, 'dashboard/admin/add_user.html', context)

def create_user(request):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('home')
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password = make_password(password)

        a = User(first_name=first_name, last_name=last_name, username=username, password=password, email=email, is_admin=True)
        a.save()
        messages.success(request, 'Admin Was Created Successfully')
        return redirect('allusers')
    else:
        messages.error(request, 'Admin Was Not Created Successfully')
        return redirect('create_user_form')

def UpdatePassword(request):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('home')
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('adminprofile')
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
