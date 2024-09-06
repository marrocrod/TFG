from django.contrib import admin
from .models import User

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'verification_status', 'is_active', 'created_at')
    actions = ['approve_users', 'reject_users']

    def approve_users(self, request, queryset):
        queryset.filter(user_type='Teacher').update(verification_status='APPROVED', is_active=True)
        self.message_user(request, "Los usuarios seleccionados han sido aprobados.")

    def reject_users(self, request, queryset):
        queryset.filter(user_type='Teacher').update(verification_status='REJECTED', is_active=False)
        self.message_user(request, "Los usuarios seleccionados han sido rechazados.")
