from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import logout,login, authenticate ,authenticate
from django.views.generic.edit import CreateView
from ..forms import LearnerSignUpForm
from ..models import User

# Shared Views

def home(request):
	return render(request, 'home.html')

def login_form(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        return render(request, 'login.html')

def logoutView(request):
	logout(request)
	return redirect('home')

def loginView(request):
    if request.user.is_authenticated:
        if request.user.is_admin or request.user.is_superuser:
            return redirect('dashboard')
        elif request.user.is_instructor:
            return redirect('instructor')
        elif request.user.is_learner:
            return redirect('learner')
        else:
            return redirect('login_form')

    if request.method == 'POST':
        # Process the login form
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            # Redirect based on role after successful login
            if user.is_admin or user.is_superuser:
                return redirect('dashboard')
            elif user.is_instructor:
                return redirect('instructor')
            elif user.is_learner:
                return redirect('learner')
            else:
                return redirect('login_form')
        else:
            messages.info(request, "Invalid Username or Password")
            return redirect('login_form')

    # If the request is not POST, render the login form
    return render(request, 'login.html')

class LearnerSignUpView(CreateView):
    model = User
    form_class = LearnerSignUpForm
    template_name = 'signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'learner'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('home')
