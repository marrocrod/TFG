from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),
    path('register/', register_view, name='register_view'),
    path('register/teacher/', register_teacher, name='register_teacher'),
    path('register/student/', register_student, name='register_student'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)