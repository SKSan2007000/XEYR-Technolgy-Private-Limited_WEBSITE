from rest_framework import serializers
from .models import (
    EventListing, EventFormField, EventRegistration,
    EventNotificationSubscriber, EventNotificationDelivery,
    EventPaymentOrder, EventRefundRecord, SocialMediaConfig,
    SkillBridgeCollegeEnquiry, SkillBridgeProfessionalApplication,
    EventFeedback, EventCertificate, EventAttendance, EventGalleryItem,
    CertificateTemplate
)


class CertificateTemplateSerializer(serializers.ModelSerializer):
    assigned_events_count = serializers.SerializerMethodField()

    class Meta:
        model = CertificateTemplate
        fields = [
            'id', 'name', 'slug', 'status', 'orientation', 'width', 'height',
            'background_type', 'background_color', 'background_gradient',
            'background_image', 'background_image_url',
            'border_style', 'border_color', 'border_width',
            'title', 'subtitle', 'description_template',
            'logo_image', 'logo_url',
            'signatory_name', 'signatory_title', 'signature_image', 'signature_url',
            'organizer_name', 'show_qr_code', 'typography', 'layout_elements',
            'is_default', 'assigned_events_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_assigned_events_count(self, obj):
        return obj.assigned_events.count()


class EventFormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventFormField
        fields = [
            'id', 'event', 'field_label', 'field_name', 'field_type',
            'is_required', 'placeholder', 'help_text', 'options', 'display_order'
        ]


class EventListingSerializer(serializers.ModelSerializer):
    form_fields = EventFormFieldSerializer(many=True, read_only=True)
    confirmed_count = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    is_registration_open = serializers.BooleanField(read_only=True)

    # Aliases for bidirectional frontend compatibility
    category = serializers.CharField(source='event_type', required=False)
    short_summary = serializers.CharField(source='short_description', required=False, allow_blank=True)
    location_type = serializers.CharField(source='mode', required=False)
    venue_name = serializers.CharField(source='venue', required=False, allow_blank=True)
    capacity = serializers.IntegerField(source='max_participants', required=False, allow_null=True)
    registration_fee = serializers.DecimalField(source='fee_amount', max_digits=10, decimal_places=2, required=False)

    can_safely_delete = serializers.BooleanField(read_only=True)

    certificate_template_name = serializers.CharField(source='certificate_template_ref.name', read_only=True, allow_null=True)

    class Meta:
        model = EventListing
        fields = [
            'id', 'title', 'slug', 'event_type', 'poster', 'poster_url',
            'short_description', 'description', 'full_description', 'event_date', 'start_time',
            'end_time', 'date_time', 'mode', 'venue', 'organizer', 'eligibility',
            'registration_deadline', 'max_participants', 'is_paid', 'fee',
            'fee_amount', 'currency', 'refund_policy', 'status', 'is_active',
            'is_published', 'highlights', 'results_summary', 'gallery_urls',
            'terms_and_conditions', 'contact_email', 'contact_phone',
            'mentors', 'schedule', 'learning_outcomes', 'prerequisites',
            'target_audience', 'guidelines', 'faqs', 'appearance',
            'joining_instructions', 'attendance_requirements',
            'certificate_enabled', 'certificate_template', 'certificate_template_ref',
            'certificate_template_name', 'certificate_custom_settings',
            'certificate_require_attendance', 'certificate_min_attendance',
            'certificate_require_feedback', 'certificate_require_activities',
            'certificate_activities_description', 'certificate_other_conditions',
            'certificate_release_date', 'feedback_enabled', 'feedback_questions',
            'is_featured', 'public_visibility', 'can_safely_delete',
            'form_fields', 'confirmed_count', 'is_completed', 'is_registration_open',
            'category', 'short_summary', 'location_type', 'venue_name', 'capacity', 'registration_fee',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EventRegistrationSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 'event_title', 'user', 'registration_reference', 'event_name',
            'full_name', 'company_or_college', 'email', 'phone', 'form_responses',
            'registration_status', 'payment_status', 'fee_paid', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'registration_reference', 'created_at']


class EventNotificationDeliverySerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    subscriber_email = serializers.CharField(source='subscriber.email', read_only=True)
    subscriber_name = serializers.CharField(source='subscriber.full_name', read_only=True)

    class Meta:
        model = EventNotificationDelivery
        fields = [
            'id', 'event', 'event_title', 'subscriber', 'subscriber_email',
            'subscriber_name', 'status', 'sent_at', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EventNotificationSubscriberSerializer(serializers.ModelSerializer):
    deliveries_count = serializers.SerializerMethodField()
    failed_deliveries_count = serializers.SerializerMethodField()
    recent_deliveries = serializers.SerializerMethodField()

    class Meta:
        model = EventNotificationSubscriber
        fields = [
            'id', 'full_name', 'email', 'categories_of_interest', 'is_active',
            'consent_given', 'subscribed_at', 'unsubscribe_token',
            'deliveries_count', 'failed_deliveries_count', 'recent_deliveries'
        ]
        read_only_fields = ['id', 'subscribed_at', 'unsubscribe_token']

    def get_deliveries_count(self, obj):
        return obj.received_notifications.filter(status='SENT').count()

    def get_failed_deliveries_count(self, obj):
        return obj.received_notifications.filter(status='FAILED').count()

    def get_recent_deliveries(self, obj):
        deliveries = obj.received_notifications.select_related('event')[:5]
        return EventNotificationDeliverySerializer(deliveries, many=True).data


class EventPaymentOrderSerializer(serializers.ModelSerializer):
    registration_ref = serializers.CharField(source='registration.registration_reference', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)

    class Meta:
        model = EventPaymentOrder
        fields = [
            'id', 'registration', 'registration_ref', 'event', 'event_title',
            'razorpay_order_id', 'razorpay_payment_id', 'amount', 'currency',
            'status', 'created_at', 'verified_at'
        ]
        read_only_fields = ['id', 'created_at']


class EventRefundRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRefundRecord
        fields = [
            'id', 'payment_order', 'registration', 'refund_amount',
            'refund_reason', 'razorpay_refund_id', 'status', 'created_at', 'processed_by'
        ]
        read_only_fields = ['id', 'created_at']


class SocialMediaConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMediaConfig
        fields = [
            'id', 'platform_key', 'platform_name', 'platform_url',
            'qr_code_image', 'is_public', 'display_order'
        ]


class SkillBridgeCollegeEnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillBridgeCollegeEnquiry
        fields = ['id', 'enquiry', 'contact_name', 'college_name', 'email', 'phone', 'preferred_service', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class SkillBridgeProfessionalApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillBridgeProfessionalApplication
        fields = ['id', 'full_name', 'email', 'phone', 'skills_can_teach', 'profile_type', 'resume_file', 'status', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class EventFeedbackSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)

    class Meta:
        model = EventFeedback
        fields = [
            'id', 'event', 'event_title', 'registration', 'user', 'full_name', 'email',
            'rating', 'content_rating', 'mentor_rating', 'organization_rating',
            'learnings', 'suggestions', 'comments', 'submitted_at'
        ]
        read_only_fields = ['id', 'submitted_at']


class EventCertificateSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_slug = serializers.CharField(source='event.slug', read_only=True)
    event_date = serializers.DateField(source='event.event_date', read_only=True)
    template_name = serializers.CharField(source='template_ref.name', read_only=True, allow_null=True)
    reissued_by_username = serializers.CharField(source='reissued_by.username', read_only=True, allow_null=True)
    download_url = serializers.SerializerMethodField()
    render_url = serializers.SerializerMethodField()
    verify_url = serializers.SerializerMethodField()

    class Meta:
        model = EventCertificate
        fields = [
            'id', 'certificate_id', 'event', 'event_title', 'event_slug', 'event_date',
            'registration', 'user', 'recipient_name', 'recipient_email', 'status',
            'issue_date', 'template_type', 'template_ref', 'template_name',
            'template_snapshot', 'organizer_name', 'signatory_title',
            'verification_token', 'reissued_at', 'reissue_reason', 'reissued_by',
            'reissued_by_username', 'revoked_at', 'revocation_reason',
            'email_delivery_status', 'email_sent_at', 'email_error',
            'download_url', 'render_url', 'verify_url', 'created_at'
        ]
        read_only_fields = ['id', 'certificate_id', 'verification_token', 'created_at']

    def get_download_url(self, obj):
        return f"/api/certificates/download/{obj.certificate_id}/"

    def get_render_url(self, obj):
        return f"/api/certificates/{obj.certificate_id}/render/"

    def get_verify_url(self, obj):
        return f"/verify-certificate/{obj.certificate_id}/"


class PublicCertificateVerificationSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_mode = serializers.CharField(source='event.mode', read_only=True)
    event_type = serializers.CharField(source='event.event_type', read_only=True)

    class Meta:
        model = EventCertificate
        fields = [
            'certificate_id', 'recipient_name', 'event_title', 'event_mode',
            'event_type', 'issue_date', 'status', 'organizer_name', 'signatory_title'
        ]


class EventAttendanceSerializer(serializers.ModelSerializer):
    participant_name = serializers.CharField(source='registration.full_name', read_only=True)
    participant_email = serializers.CharField(source='registration.email', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)

    class Meta:
        model = EventAttendance
        fields = [
            'id', 'event', 'event_title', 'registration', 'user', 'participant_name',
            'participant_email', 'attended', 'attendance_percentage', 'marked_at', 'marked_by'
        ]
        read_only_fields = ['id', 'marked_at']


class EventGalleryItemSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True, allow_null=True)

    class Meta:
        model = EventGalleryItem
        fields = [
            'id', 'event', 'event_title', 'title', 'image', 'image_url',
            'caption', 'alt_text', 'category', 'display_order', 'is_public', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

