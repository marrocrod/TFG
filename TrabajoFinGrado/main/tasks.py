from celery import shared_task
from django.utils import timezone
from .models import User

@shared_task
def delete_unactivated_users():
    expiration_time = timezone.now() - timezone.timedelta(hours=1)
    unactivated_users = User.objects.filter(is_active=False, created_at__lt=expiration_time)
    unactivated_users.delete()
