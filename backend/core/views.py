from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
import json
import re
from django.conf import settings
from .models import User, UserProfile, UserRole, AuditLog, Notification, SystemSetting
from .serializers import (
    UserSerializer, UserProfileSerializer, ParticipantSignupSerializer,
    AuditLogSerializer, NotificationSerializer, SystemSettingSerializer
)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


from django.core.cache import cache


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Brute-force protection: Check IP + username lockout
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()
        lockout_key = f"login_lockout_{ip}_{username}"
        fail_key = f"login_failures_{ip}_{username}"

        if cache.get(lockout_key):
            AuditLog.log('LOGIN_LOCKED_OUT', 'User', username, details={'ip': ip}, request=request)
            return Response({
                'error': 'Too many failed login attempts. Login temporarily locked for 15 minutes.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                return Response({'error': 'User account is inactive.'}, status=status.HTTP_403_FORBIDDEN)
            # Reset failure count on valid login
            cache.delete(fail_key)
            cache.delete(lockout_key)

            login(request, user)
            AuditLog.log('USER_LOGIN', 'User', user.id, user=user, details={'username': user.username}, request=request)
            return Response({
                'message': 'Login successful.',
                'user': UserSerializer(user).data
            })

        # Track failure
        failures = cache.get(fail_key, 0) + 1
        cache.set(fail_key, failures, 900)
        if failures >= 5:
            cache.set(lockout_key, True, 900)
            AuditLog.log('BRUTE_FORCE_LOCKOUT_TRIGGERED', 'User', username, details={'ip': ip, 'attempts': failures}, request=request)

        return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        AuditLog.log('USER_LOGOUT', 'User', request.user.id, user=request.user, details={}, request=request)
        logout(request)
        return Response({'message': 'Logged out successfully.'})


class UserListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'BUSINESS_ADMIN']):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        users = User.objects.all().order_by('username')
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'BUSINESS_ADMIN']):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'BUSINESS_ADMIN')

        if not username or not password:
            return Response({'error': 'Username and password required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            password=password,
            email=data.get('email', ''),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=role,
            phone=data.get('phone', ''),
            department=data.get('department', 'Operations')
        )
        AuditLog.log('USER_CREATED', 'User', user.id, user=request.user, details={'username': username, 'role': role}, request=request)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class AuditLogListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        logs = AuditLog.objects.select_related('user').all()[:100]
        return Response(AuditLogSerializer(logs, many=True).data)


class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            user__isnull=True
        ) | Notification.objects.filter(user=request.user)
        notifications = notifications.order_by('-created_at')[:50]
        return Response(NotificationSerializer(notifications, many=True).data)


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        if pk:
            Notification.objects.filter(id=pk).update(is_read=True)
        else:
            Notification.objects.filter(user=request.user).update(is_read=True)
        return Response({'message': 'Notifications marked as read.'})


class SystemSettingListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        settings_qs = SystemSetting.objects.all()
        return Response(SystemSettingSerializer(settings_qs, many=True).data)

    def post(self, request):
        if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'BUSINESS_ADMIN']):
            return Response({'error': 'Only Administrators can modify system settings.'}, status=status.HTTP_403_FORBIDDEN)

        # Batch update support
        batch_settings = request.data.get('settings')
        if isinstance(batch_settings, dict):
            updated = []
            for k, v in batch_settings.items():
                if not isinstance(k, str) or not k.strip():
                    continue
                k_clean = k.strip()
                v_clean = str(v) if not isinstance(v, (dict, list)) else json.dumps(v)
                s, _ = SystemSetting.objects.update_or_create(
                    key=k_clean,
                    defaults={'value': v_clean}
                )
                updated.append(s)
            AuditLog.log('SYSTEM_SETTINGS_BATCH_UPDATED', 'SystemSetting', 'BATCH', user=request.user, details={'keys': list(batch_settings.keys())}, request=request)
            return Response({'message': f'Successfully updated {len(updated)} system settings.', 'settings': SystemSettingSerializer(updated, many=True).data})

        # Single key update
        key = request.data.get('key')
        value = request.data.get('value')
        if not key:
            return Response({'error': 'Setting key is required.'}, status=status.HTTP_400_BAD_REQUEST)

        val_str = str(value) if not isinstance(value, (dict, list)) else json.dumps(value)
        setting, created = SystemSetting.objects.update_or_create(
            key=key.strip(),
            defaults={'value': val_str, 'description': request.data.get('description', '')}
        )
        AuditLog.log('SYSTEM_SETTING_UPDATED', 'SystemSetting', setting.id, user=request.user, details={'key': key}, request=request)
        return Response(SystemSettingSerializer(setting).data)


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.db import connection
        from django.conf import settings
        db_healthy = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                db_healthy = (row[0] == 1)
        except Exception:
            db_healthy = False

        engine_name = 'postgresql' if 'postgresql' in settings.DATABASES['default']['ENGINE'] else 'sqlite'
        return Response({
            'status': 'healthy' if db_healthy else 'unhealthy',
            'database': 'healthy' if db_healthy else 'unhealthy',
            'engine': engine_name,
            'service': 'XEYR Technologies Enterprise Backend'
        })


# ==============================================================================
# PARTICIPANT AUTHENTICATION & PROFILE
# ==============================================================================

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ParticipantSignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ParticipantSignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        username = data['username'].strip().lower()
        email = data['email'].strip().lower()

        if User.objects.filter(username=username).exists():
            return Response({'error': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'A user with this email address already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        full_name = data.get('full_name', '').strip()
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=data['password'],
            first_name=first_name,
            last_name=last_name,
            role=UserRole.PARTICIPANT,
            phone=data.get('phone', ''),
            department=data.get('participant_category', 'Student')
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.college_or_organization = data.get('college_or_organization', '')
        profile.save()
        user.profile = profile

        # Link past registrations matching this email
        from events_mgmt.models import EventRegistration
        EventRegistration.objects.filter(email__iexact=email, user__isnull=True).update(user=user)

        # Automatically log the participant in
        login(request, user)
        if hasattr(request, 'session'):
            request.session.save()
        AuditLog.log('PARTICIPANT_SIGNUP', 'User', user.id, user=user, details={'username': user.username}, request=request)

        return Response({
            'message': 'Account created and authenticated successfully.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class ParticipantProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response(UserProfileSerializer(profile).data)

    def put(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        data = request.data

        # Update User fields if provided
        if 'full_name' in data and data['full_name'].strip():
            parts = data['full_name'].strip().split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
        if 'phone' in data:
            user.phone = data['phone'].strip()
        user.save()

        # Update Profile fields
        allowed_profile_fields = [
            'avatar_url', 'college_or_organization', 'department', 'year_of_study',
            'designation', 'city', 'bio', 'skills', 'portfolio_url', 'github_url',
            'linkedin_url', 'resume_url', 'consent_public_leaderboard', 'notification_preferences'
        ]
        for field in allowed_profile_fields:
            if field in data:
                setattr(profile, field, data[field])

        profile.save()
        AuditLog.log('PARTICIPANT_PROFILE_UPDATE', 'UserProfile', profile.id, user=user, details={}, request=request)
        return Response(UserProfileSerializer(profile).data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({'error': 'Old password and new password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({'error': 'New password must be at least 8 characters long.'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(old_password):
            return Response({'error': 'Incorrect current password.'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        login(request, request.user)  # Keep session active
        AuditLog.log('PASSWORD_CHANGED', 'User', request.user.id, user=request.user, details={}, request=request)

        return Response({'message': 'Password updated successfully.'})


class PublicLeaderboardView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from events_mgmt.models import EventRegistration, EventCertificate
        profiles = UserProfile.objects.filter(
            consent_public_leaderboard=True,
            user__is_active=True
        ).select_related('user').order_by('-verified_points', '-created_at')[:50]

        leaderboard = []
        for idx, p in enumerate(profiles, start=1):
            completed_events = EventRegistration.objects.filter(
                user=p.user,
                registration_status='CONFIRMED',
                event__status='COMPLETED'
            ).count()
            cert_count = EventCertificate.objects.filter(user=p.user, status='ISSUED').count()

            # Dynamic score calculation: points or (completed_events * 50 + cert_count * 100)
            score = p.verified_points if p.verified_points > 0 else (completed_events * 50 + cert_count * 100)

            name = p.user.get_full_name() or p.user.username
            leaderboard.append({
                'rank': idx,
                'display_name': name,
                'username': p.user.username,
                'avatar_url': p.avatar_url or '',
                'score': score,
                'completed_events_count': completed_events,
                'certificates_count': cert_count,
                'college_or_organization': p.college_or_organization,
                'skills': p.skills
            })

        # Re-sort by final computed score
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        for i, item in enumerate(leaderboard, start=1):
            item['rank'] = i

        return Response({
            'count': len(leaderboard),
            'leaderboard': leaderboard
        })


class PublicSystemSettingsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from events_mgmt.models import SocialMediaConfig

        def get_setting(key, fallback):
            s = SystemSetting.objects.filter(key=key).first()
            if s and s.value and s.value.strip():
                return s.value.strip()
            return fallback

        def get_json_setting(key, fallback):
            val = get_setting(key, None)
            if val:
                try:
                    return json.loads(val)
                except Exception:
                    pass
            return fallback

        base_url = get_setting('PUBLIC_BASE_URL', getattr(settings, 'PUBLIC_BASE_URL', 'http://localhost:8080')).rstrip('/')
        company_website_url = get_setting('COMPANY_WEBSITE_URL', base_url)
        events_portal_url = get_setting('EVENTS_PORTAL_URL', f"{base_url}/events/")

        default_services = [
            {
                'id': 'ai_ml',
                'title': 'AI and Machine Learning',
                'description': 'Practical machine learning models, predictive systems, and intelligent automation built for business operations.',
                'icon': '✧',
                'link': f"{company_website_url}#services"
            },
            {
                'id': 'software_dev',
                'title': 'Software Development',
                'description': 'End-to-end commercial web applications, bespoke business platforms, and robust modern software architectures.',
                'icon': '⌘',
                'link': f"{company_website_url}#services"
            },
            {
                'id': 'saas_dev',
                'title': 'SaaS Product Development',
                'description': 'Scalable multi-tenant cloud software, recurring subscription architectures, and digital products.',
                'icon': '☁',
                'link': f"{company_website_url}#services"
            },
            {
                'id': 'automation',
                'title': 'Automation Solutions',
                'description': 'Workflow optimizations, robotic process integrations, and modern AI agent pipelines.',
                'icon': '⚙',
                'link': f"{company_website_url}#services"
            },
            {
                'id': 'iot_tech',
                'title': 'IoT and Smart Technology',
                'description': 'Connected device telemetry, smart sensor interfaces, and modern embedded intelligence.',
                'icon': '📡',
                'link': f"{company_website_url}#services"
            },
            {
                'id': 'tech_events',
                'title': 'Technology Events and Learning Opportunities',
                'description': 'Hands-on engineering workshops, expert speaker sessions, and practical skill-building.',
                'icon': '✦',
                'link': events_portal_url
            }
        ]

        default_visibility = {
            'who_we_are': True,
            'what_we_do': True,
            'contact_us': True,
            'quick_links': True,
            'leaderboard': True,
            'gallery': True
        }

        # Social media links
        try:
            social_qs = SocialMediaConfig.objects.filter(is_public=True).order_by('display_order', 'platform_name')
            social_links = [
                {
                    'platform_key': s.platform_key,
                    'platform_name': s.platform_name,
                    'platform_url': s.platform_url,
                    'qr_code_url': s.qr_code_image.url if s.qr_code_image else ''
                }
                for s in social_qs
            ]
        except Exception:
            social_links = []

        return Response({
            'public_base_url': base_url,
            'company_website_url': company_website_url,
            'events_portal_url': events_portal_url,
            'company_name': get_setting('COMPANY_NAME', 'XEYR Technologies Private Limited'),
            'company_intro': get_setting(
                'COMPANY_INTRO',
                'XEYR Technologies Private Limited is focused on delivering technology-driven solutions through software development, artificial intelligence, automation, SaaS products, and innovative digital experiences.'
            ),
            'tagline': get_setting('COMPANY_TAGLINE', 'Ideas | Technology | Real Impact'),
            'contact_email': get_setting('CONTACT_EMAIL', 'xeyrtechnologies@gmail.com'),
            'contact_phone': get_setting('CONTACT_PHONE', '+91 80562 53897'),
            'logo_asset_url': get_setting('LOGO_ASSET_URL', '/assets/xeyr-symbol.png'),
            'logo_wordmark_url': get_setting('LOGO_WORDMARK_URL', '/assets/xeyr-wordmark.png'),

            # Section A — Who We Are
            'who_we_are_heading': get_setting('WHO_WE_ARE_HEADING', 'Who We Are'),
            'who_we_are_description': get_setting(
                'WHO_WE_ARE_DESCRIPTION',
                'XEYR Technologies Private Limited is focused on delivering technology-driven solutions through software development, artificial intelligence, automation, SaaS products, and innovative digital experiences. Through our Events Portal, we aim to make it easier for participants to discover events, explore learning opportunities, and connect with technology-focused communities.'
            ),

            # Section B — What We Do
            'what_we_do_heading': get_setting('WHAT_WE_DO_HEADING', 'What We Do'),
            'services': get_json_setting('SERVICES_LIST', default_services),

            # Section C — Contact Us
            'contact_heading': get_setting('CONTACT_HEADING', 'Get in Touch'),

            # Section D — Quick Links
            'quick_links_heading': get_setting('QUICK_LINKS_HEADING', 'Quick Links'),

            # Footer
            'footer_tagline': get_setting('FOOTER_TAGLINE', 'Ideas. Technology. Real Impact.'),
            'footer_description': get_setting(
                'FOOTER_DESCRIPTION',
                'XEYR Technologies Private Limited develops enterprise software, intelligent automation, and hands-on learning experiences.'
            ),
            'footer_column_headings': get_json_setting('FOOTER_COLUMN_HEADINGS', {
                'col1': 'Branding',
                'col2': 'Explore',
                'col3': 'Company',
                'col4': 'Policies and Support'
            }),

            # Section Visibility
            'section_visibility': get_json_setting('SECTION_VISIBILITY', default_visibility),

            # Approved Social Media
            'social_links': social_links
        })


