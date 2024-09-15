from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from .views import CustomLoginView
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView


urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('register/teacher/', register_teacher, name='register_teacher'),
    path('register/student/', register_student, name='register_student'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
    path('resend_activation_email/', resend_activation_email, name='resend_activation_email'),
    path('activation_resent/', TemplateView.as_view(template_name='register/activation_resent.html'), name='activation_resent'),  
    path('password_reset/', password_reset_request, name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='recovery/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(template_name='recovery/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='recovery/password_reset_complete.html'), name='password_reset_complete'),
    path('username_recovery/', username_recovery_request, name='username_recovery'),
    path('username_recovery_done/', TemplateView.as_view(template_name='recovery/username_recovery_done.html'), name='username_recovery_done'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('session-expired/', session_expired, name='session_expired'),
    path('rejected-teacher/', rejected_teacher, name='rejected_teacher'),
    path('pending-teacher/', pending_teacher, name='pending_teacher'),
    path('user_profile/', user_profile, name='user_profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('chat/<int:chat_id>/', chat_view, name='chat'),  # Ruta con chat_id
    path('chat/', chat_view, name='chat_default'),        # Ruta sin chat_id
    path('chat/archived/<int:chat_id>/', archived_chat_view, name='archived_chat'),
    path('chat/archive/<int:chat_id>/', archive_chat, name='archive_chat'),
    path('chats/archived/', archived_chats_list, name='archived_chats_list'),  # Lista de chats archivados
    path('exercises/', generate_exercises_view, name='exercises'),
    path('exams/', generate_exam_view, name='exams'),
    path('generate-exercises/', generate_exercises, name='generate_exercises'),
    path('exercise-set/<int:set_id>/', exercise_set_detail, name='exercise_set_detail'),
    path('generate-exam/', generate_exam, name='generate_exam'),
    path('exam/<int:exam_id>/', exam_detail, name='exam_detail'),
    path('exam/<int:exam_id>/submit/', submit_exam, name='submit_exam'),
    path('exam/<int:exam_id>/archived/', archived_exam, name='archived_exam'),
    path('calendar/', calendar_view, name='calendar'),
    path('calendar/day/<str:date>/', day_view, name='day-view'),
    path('calendar/edit/<int:event_id>/', edit_event, name='edit-event'),  
    path('calendar/delete/<int:event_id>/', delete_event, name='delete-event'),  
    path('api/calendar-events/', calendar_events, name='calendar-events'),  
    path('students/<int:student_id>/', student_detail, name='student_detail'),
    path('teachers/', teacher_list, name='teacher_list'),
    path('forums/', forum_home, name='forum_home'),
    path('forums/create/', create_forum, name='create_forum'),
    path('forums/<int:forum_id>/', view_forum, name='view_forum'),
    path('forums/<int:forum_id>/close/', close_forum, name='close_forum'),

]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  