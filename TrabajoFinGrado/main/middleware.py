from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import logout
from .views import delete_unactivated_users
from django.urls import reverse, NoReverseMatch, resolve
from django.shortcuts import redirect


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            last_activity = request.session.get('last_activity')

            if not last_activity:
                request.session['last_activity'] = now.isoformat()
            else:
                last_activity_time = timezone.datetime.fromisoformat(last_activity)

                if now - last_activity_time > timedelta(seconds=settings.SESSION_COOKIE_AGE):
                    logout(request)
                    request.session['session_expired'] = True  
                else:
                    request.session['last_activity'] = now.isoformat()

        response = self.get_response(request)
        return response


class CleanupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        delete_unactivated_users()
        response = self.get_response(request)
        return response

class PendingTeacherMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.user_type == 'Teacher' and request.user.verification_status == 'PENDING':
                allowed_paths = [
                    reverse('home'),
                    reverse('pending_teacher'),  
                    reverse('logout'),  
                ]

                if request.path not in allowed_paths:
                    return redirect('home')  
        
        response = self.get_response(request)
        return response

class RejectedTeacherMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.user_type == 'Teacher' and request.user.verification_status == 'REJECTED':
                allowed_paths = [
                    reverse('home'),
                    reverse('rejected_teacher'),  
                    reverse('logout'),  
                ]

                if request.path not in allowed_paths:
                    return redirect('home')  
        
        response = self.get_response(request)
        return response



class TeacherAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_teacher_paths = [
            reverse('home'),
            reverse('logout'),
            reverse('rejected_teacher'),
            reverse('pending_teacher'),
            reverse('user_profile'),
            reverse('edit_profile'),
            reverse('archived_chat', kwargs={'chat_id': 1}),  
            reverse('archive_chat', kwargs={'chat_id': 1}),
            reverse('archived_chats_list'),
            reverse('archived_exam', kwargs={'exam_id': 1}),
            reverse('student_detail', kwargs={'student_id': 1}),
            reverse('forum_home'),
            reverse('create_forum'),
            reverse('view_forum', kwargs={'forum_id': 1}),
            reverse('close_forum', kwargs={'forum_id': 1}),
        ]
        
        allowed_dynamic_paths = [
            '/chat/archived/',
            '/chat/archive/',
            '/exam/',
            '/students/',
            '/forums/',
        ]
        
        if request.user.is_authenticated and request.user.user_type == 'Teacher':
            if (request.path not in allowed_teacher_paths and 
                not any(request.path.startswith(dynamic_path) for dynamic_path in allowed_dynamic_paths)):
                return redirect('home')  
        
        response = self.get_response(request)
        return response
    


class StudentRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.restricted_paths = [
            'register', 'register_teacher', 'register_student',
            'resend_activation_email', 'activation_resent',
            'password_reset', 'password_reset_done',
            'username_recovery', 'username_recovery_done',
            'login', 'session_expired', 'rejected_teacher',
            'pending_teacher'
        ]
        self.restricted_named_paths = [
            'student_detail', 'activate', 'password_reset_confirm', 'password_reset_complete'
        ]

    def __call__(self, request):
        path = request.path_info.lstrip('/')
        
        if request.user.is_authenticated and request.user.user_type == 'Student':
            for restricted_path in self.restricted_paths:
                if path.startswith(restricted_path):
                    return redirect('home')

            try:
                resolved_url_name = resolve(request.path_info).url_name
                if resolved_url_name in self.restricted_named_paths:
                    return redirect('home')
            except NoReverseMatch:
                pass  
        
        response = self.get_response(request)
        return response
