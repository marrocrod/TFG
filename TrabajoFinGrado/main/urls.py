from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from .views import CustomLoginView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('register/teacher/', register_teacher, name='register_teacher'),
    path('register/student/', register_student, name='register_student'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('user_profile/', user_profile, name='user_profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('chat/<int:chat_id>/', chat_view, name='chat'),  # Ruta con chat_id
    path('chat/', chat_view, name='chat_default'),        # Ruta sin chat_id
    path('chat/archived/<int:chat_id>/', archived_chat_view, name='archived_chat'),
    path('chat/archive/<int:chat_id>/', archive_chat, name='archive_chat'),
    path('chats/archived/', archived_chats_list, name='archived_chats_list'),  # Lista de chats archivados
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)