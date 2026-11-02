from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditLog, Notification, SystemSetting

admin.site.site_header = "XEYR Technologies Administration"
admin.site.site_title = "XEYR Management Portal"
admin.site.index_title = "XEYR Business Operations & Database Models"
admin.site.site_url = "/dashboard/"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'department')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('username',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('XEYR Role & Profile', {'fields': ('role', 'phone', 'department')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'entity_type', 'entity_id', 'user', 'ip_address', 'timestamp')
    list_filter = ('action', 'entity_type', 'timestamp')
    search_fields = ('action', 'entity_type', 'entity_id', 'ip_address')
    readonly_fields = ('action', 'entity_type', 'entity_id', 'user', 'ip_address', 'details', 'timestamp')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message')


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')
    search_fields = ('key', 'description')

