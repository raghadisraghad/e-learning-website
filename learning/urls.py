from django.urls import path
from .views import main,instructor,learner,admin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # Shared URLs   
    path('', main.home, name='home'),
    path('signup/', main.LearnerSignUpView.as_view(), name='signup'),
    path('login_form/', main.login_form, name='login_form'),
    path('login/', main.loginView, name='login'),
    path('logout/', main.logoutView, name='logout'),

    # # Admin URLs
    path('dashboard/', login_required(admin.dashboard), name='dashboard'),
    path('course/', login_required(admin.course), name='course'),
    path('deletecourse/<int:course_id>/', admin.DeleteCourse, name='deletecourse'),
    path('addinstructor/', login_required(admin.InstructorSignUpView.as_view()), name='addinstructor'),
    path('addlearner/', login_required(admin.AdminLearner.as_view()), name='addlearner'),
    path('addanonce/', login_required(admin.AdminCreateAnnonce.as_view()), name='addanonce'),
    path('allannonce/', login_required(admin.AdminAllAnnonce.as_view()), name='allannonce'),
    path('deleteannonce/<int:pk>', login_required(admin.AdminDeleteAnnonce.as_view()), name='deleteannonce'),
    path('allusers/', login_required(admin.ListUserView.as_view()), name='allusers'),
    path('admindeleteuser/<int:pk>', login_required(admin.AdminDeleteUser.as_view()), name='admindeleteuser'),
    path('create_user_form/', login_required(admin.create_user_form), name='create_user_form'),
    path('create_user/', login_required(admin.create_user), name='create_user'),
    path('makeadmin/', login_required(admin.promote_to_admin), name='makeadmin'),
    path('removeadmin/', login_required(admin.remove_admin), name='removeadmin'),
    path('adminprofile/', login_required(admin.AdminProfile), name='adminprofile'),
    path('updatepassword/', login_required(admin.UpdatePassword), name='updatepassword'),
    path('adminclearnotification/', login_required(admin.ClearNotification), name='adminclearnotification'),
    path('adminnotification/', login_required(admin.Notification.as_view()), name='adminnotification'),

    # # Instructor URLs
    path('instructor/', login_required(instructor.home_instructor), name='instructor'),
    path('annonce/', login_required(instructor.InstructorCreateAnnonce.as_view()), name='annonce'),
    path('instructorallannonce/', login_required(instructor.InstructorAllAnnonce.as_view()), name='instructorallannonce'),
    path('quiz_add/', login_required(instructor.QuizCreateView.as_view()), name='quiz_add'),
    path('llist_quiz/', login_required(instructor.QuizListView.as_view()), name='quiz_change_list'),
    path('quiz/<int:pk>/results/', login_required(instructor.QuizResultsView.as_view()), name='quiz_results'),
    path('quiz/<int:pk>/delete/', login_required(instructor.QuizDeleteView.as_view()), name='quiz_delete'),
    path('quizupdate/<int:pk>/', login_required(instructor.QuizUpdateView.as_view()), name='quiz_change'),
    path('question_add/<int:pk>', login_required(instructor.question_add), name='question_add'),
    path('quiz/<int:quiz_pk>/<int:question_pk>/', login_required(instructor.question_change), name='question_change'),
    path('quiz/<int:quiz_pk>/question/<int:question_pk>/delete/', login_required(instructor.QuestionDeleteView.as_view()), name='question_delete'),
    path('tutorial/', login_required(instructor.tutorial), name='tutorial'),
    path('tutorial/<int:tutorial_id>/delete/', login_required(instructor.deleteTutorial), name='deleteTutorial'),
    path('listnotes/', login_required(instructor.LNotesList.as_view()), name='lnotes'),
    path('iadd_notes/', login_required(instructor.iadd_notes), name='iadd_notes'),  
    path('update_file/<int:pk>', login_required(instructor.update_file), name='update_file'),
    path('publish_notes/', login_required(instructor.publish_notes), name='publish_notes'),
    path('post/', login_required(instructor.publish_tutorial),name='publish_tutorial'),
    path('itutorial/', login_required(instructor.itutorial),name='itutorial'),
    path('instructorprofile/', login_required(instructor.InstructorProfile), name='instructorprofile'),
    path('updatepassword/', login_required(instructor.UpdatePassword), name='updatepassword'),
    path('instructorclearnotification/', login_required(instructor.ClearNotification), name='instructorclearnotification'),
    path('instructornotification/', login_required(instructor.Notification.as_view()), name='instructornotification'),

    # # Learner URl's
    path('learner/', login_required(learner.home_learner),name='learner'),
    path('learnerallannonce/', login_required(learner.LearnerAllAnnonce.as_view()), name='learnerallannonce'),
    path('clearnotification/', login_required(learner.ClearNotification), name='clearnotification'),
    path('notification/', login_required(learner.Notification.as_view()), name='notification'),
    path('learnerprofile/', login_required(learner.LearnerProfile), name='learnerprofile'),
    path('learnerupdatepassword/', login_required(learner.LearnerUpdatePassword), name='learnerupdatepassword'),
    path('grades/', login_required(learner.LNotesList.as_view()), name='grades'),
    path('ltutorial/', login_required(learner.ltutorial),name='ltutorial'),
    path('tutorials/<int:pk>/', login_required(learner.LTutorialDetail.as_view()), name = "tutorial-detail"),
    path('interests/', login_required(learner.LearnerInterestsView.as_view()), name='interests'),
    path('learner_quiz/', login_required(learner.LQuizListView.as_view()), name='lquiz_list'),
    path('taken/', login_required(learner.TakenQuizListView.as_view()), name='taken_quiz_list'),
    path('quiz/<int:pk>/', login_required(learner.take_quiz), name='take_quiz'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)