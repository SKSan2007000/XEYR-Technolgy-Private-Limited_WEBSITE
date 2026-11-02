from rest_framework import serializers
from .models import User, UserProfile, AuditLog, Notification, SystemSetting


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'full_name', 'email', 'avatar', 'avatar_url',
            'college_or_organization', 'department', 'year_of_study', 'designation',
            'city', 'bio', 'skills', 'portfolio_url', 'github_url', 'linkedin_url',
            'resume_file', 'resume_url', 'verified_points', 'consent_public_leaderboard',
            'notification_preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verified_points', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'department', 'is_active', 'profile']
        read_only_fields = ['id']


class ParticipantSignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    participant_category = serializers.CharField(max_length=50, required=False, default='Student')
    college_or_organization = serializers.CharField(max_length=200, required=False, allow_blank=True)



class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_name', 'user_role', 'action', 'entity_type', 'entity_id', 'details', 'ip_address', 'timestamp']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'notification_type', 'link', 'is_read', 'created_at']


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['id', 'key', 'value', 'description', 'updated_at']
