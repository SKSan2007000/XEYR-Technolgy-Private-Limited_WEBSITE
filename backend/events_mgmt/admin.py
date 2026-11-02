from django.contrib import admin
from .models import (
    EventListing, EventFormField, EventRegistration, EventPaymentOrder,
    EventRefundRecord, EventNotificationSubscriber, EventNotificationDelivery,
    SocialMediaConfig, SkillBridgeCollegeEnquiry, SkillBridgeProfessionalApplication
)


class EventFormFieldInline(admin.TabularInline):
    model = EventFormField
    extra = 0


@admin.register(EventListing)
class EventListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'status', 'event_date', 'mode', 'fee', 'is_paid', 'is_published')
    list_filter = ('status', 'event_type', 'is_paid', 'is_published', 'mode')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EventFormFieldInline]


@admin.register(EventFormField)
class EventFormFieldAdmin(admin.ModelAdmin):
    list_display = ('event', 'field_label', 'field_name', 'field_type', 'is_required', 'display_order')
    list_filter = ('field_type', 'is_required', 'event')
    search_fields = ('field_label', 'field_name', 'event__title')


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('registration_reference', 'full_name', 'email', 'phone', 'event_name', 'registration_status', 'payment_status', 'created_at')
    list_filter = ('registration_status', 'payment_status', 'created_at')
    search_fields = ('registration_reference', 'full_name', 'email', 'phone', 'event_name')
    readonly_fields = ('registration_reference', 'created_at')


@admin.register(EventPaymentOrder)
class EventPaymentOrderAdmin(admin.ModelAdmin):
    list_display = ('razorpay_order_id', 'razorpay_payment_id', 'amount', 'currency', 'status', 'created_at', 'verified_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('razorpay_order_id', 'razorpay_payment_id')
    readonly_fields = ('razorpay_order_id', 'created_at', 'verified_at')


@admin.register(EventRefundRecord)
class EventRefundRecordAdmin(admin.ModelAdmin):
    list_display = ('payment_order', 'registration', 'refund_amount', 'status', 'created_at', 'processed_by')
    list_filter = ('status', 'created_at')
    search_fields = ('razorpay_refund_id', 'refund_reason', 'registration__registration_reference')


@admin.register(EventNotificationSubscriber)
class EventNotificationSubscriberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'categories_of_interest', 'is_active', 'consent_given', 'subscribed_at')
    list_filter = ('is_active', 'consent_given', 'subscribed_at')
    search_fields = ('full_name', 'email')
    readonly_fields = ('unsubscribe_token', 'subscribed_at')


@admin.register(EventNotificationDelivery)
class EventNotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ('event', 'subscriber', 'status', 'sent_at', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('event__title', 'subscriber__email')


@admin.register(SocialMediaConfig)
class SocialMediaConfigAdmin(admin.ModelAdmin):
    list_display = ('platform_key', 'platform_name', 'platform_url', 'is_public', 'display_order')
    list_filter = ('is_public',)
    search_fields = ('platform_key', 'platform_name')


@admin.register(SkillBridgeCollegeEnquiry)
class SkillBridgeCollegeEnquiryAdmin(admin.ModelAdmin):
    list_display = ('college_name', 'contact_name', 'email', 'phone', 'preferred_service', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('college_name', 'contact_name', 'email')


@admin.register(SkillBridgeProfessionalApplication)
class SkillBridgeProfessionalApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'profile_type', 'status', 'created_at')
    list_filter = ('profile_type', 'status', 'created_at')
    search_fields = ('full_name', 'email', 'skills_can_teach')

