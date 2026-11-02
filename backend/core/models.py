from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class UserRole(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Administrator'
    BUSINESS_ADMIN = 'BUSINESS_ADMIN', 'Business Administrator'
    SALES_CRM = 'SALES_CRM', 'Sales or CRM Executive'
    ACCOUNT_MANAGER = 'ACCOUNT_MANAGER', 'Account Manager'
    PROJECT_MANAGER = 'PROJECT_MANAGER', 'Project Manager'
    DEVELOPER = 'DEVELOPER', 'Developer'
    FINANCE_EXECUTIVE = 'FINANCE_EXECUTIVE', 'Finance Executive'
    READONLY_ANALYST = 'READONLY_ANALYST', 'Read-Only Analyst'
    PARTICIPANT = 'PARTICIPANT', 'Participant / Student'


class User(AbstractUser):
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.BUSINESS_ADMIN,
        help_text="Role determining permissions across the XEYR Business OS"
    )
    phone = models.CharField(max_length=20, blank=True, default='')
    department = models.CharField(max_length=100, blank=True, default='Operations')

    class Meta:
        ordering = ['username']

    def __str__(self):
        full = self.get_full_name()
        return f"{full or self.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.is_superuser or self.role == UserRole.SUPER_ADMIN

    @property
    def is_admin_level(self):
        return self.is_superuser or self.role in [UserRole.SUPER_ADMIN, UserRole.BUSINESS_ADMIN]

    @property
    def can_qualify_or_reject(self):
        return self.is_superuser or self.role in [
            UserRole.SUPER_ADMIN, UserRole.BUSINESS_ADMIN, UserRole.SALES_CRM, UserRole.ACCOUNT_MANAGER
        ]

    @property
    def can_manage_requirements(self):
        return self.is_superuser or self.role in [
            UserRole.SUPER_ADMIN, UserRole.BUSINESS_ADMIN, UserRole.ACCOUNT_MANAGER, UserRole.PROJECT_MANAGER
        ]

    @property
    def can_generate_handover(self):
        return self.is_superuser or self.role in [
            UserRole.SUPER_ADMIN, UserRole.BUSINESS_ADMIN, UserRole.PROJECT_MANAGER
        ]

    @property
    def can_manage_finance(self):
        return self.is_superuser or self.role in [
            UserRole.SUPER_ADMIN, UserRole.BUSINESS_ADMIN, UserRole.FINANCE_EXECUTIVE
        ]


class AuditLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        username = self.user.username if self.user else "System"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {username} -> {self.action} on {self.entity_type} #{self.entity_id}"

    @classmethod
    def log(cls, action, entity_type, entity_id, user=None, details=None, request=None):
        ip = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            if not user and request.user and request.user.is_authenticated:
                user = request.user

        return cls.objects.create(
            user=user if (user and user.is_authenticated) else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            details=details or {},
            ip_address=ip
        )


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Target user, or null for broadcast to all admin staff"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default='SYSTEM')
    link = models.CharField(max_length=255, blank=True, default='')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification: {self.title} ({'Read' if self.is_read else 'Unread'})"


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    avatar_url = models.CharField(max_length=500, blank=True, default='')
    college_or_organization = models.CharField(max_length=200, blank=True, default='')
    department = models.CharField(max_length=150, blank=True, default='')
    year_of_study = models.CharField(max_length=50, blank=True, default='')
    designation = models.CharField(max_length=150, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    skills = models.CharField(max_length=300, blank=True, default='')
    portfolio_url = models.URLField(max_length=300, blank=True, default='')
    github_url = models.URLField(max_length=300, blank=True, default='')
    linkedin_url = models.URLField(max_length=300, blank=True, default='')
    resume_file = models.FileField(upload_to='participant_resumes/', blank=True, null=True)
    resume_url = models.CharField(max_length=500, blank=True, default='')
    verified_points = models.PositiveIntegerField(default=0)
    consent_public_leaderboard = models.BooleanField(default=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-verified_points', 'user__username']

    def __str__(self):
        return f"Profile: {self.user.username} ({self.verified_points} pts)"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
