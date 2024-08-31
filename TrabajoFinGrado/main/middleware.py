from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import logout

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
                    request.session['session_expired'] = True  # Marca la sesión como expirada
                else:
                    request.session['last_activity'] = now.isoformat()

        response = self.get_response(request)
        return response
