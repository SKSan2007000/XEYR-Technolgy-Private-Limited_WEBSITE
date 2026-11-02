from django.contrib import admin
from .models import Enquiry, EnquiryQualification, EnquiryRejection, CRMActivity


class CRMActivityInline(admin.TabularInline):
    model = CRMActivity
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('reference_id', 'client_name', 'service_type', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'service_type', 'created_at')
    search_fields = ('reference_id', 'client_name', 'email', 'phone', 'project_title')
    readonly_fields = ('reference_id', 'created_at', 'updated_at')
    inlines = [CRMActivityInline]


@admin.register(EnquiryQualification)
class EnquiryQualificationAdmin(admin.ModelAdmin):
    list_display = ('enquiry', 'decision', 'estimated_project_value', 'budget_confirmed', 'timeline_confirmed', 'qualified_at')
    list_filter = ('budget_confirmed', 'timeline_confirmed', 'qualified_at')
    search_fields = ('enquiry__reference_id', 'enquiry__client_name', 'decision')


@admin.register(EnquiryRejection)
class EnquiryRejectionAdmin(admin.ModelAdmin):
    list_display = ('enquiry', 'category', 'rejected_by', 'rejected_at')
    list_filter = ('category', 'rejected_at')
    search_fields = ('enquiry__reference_id', 'enquiry__client_name', 'reason_detail')


@admin.register(CRMActivity)
class CRMActivityAdmin(admin.ModelAdmin):
    list_display = ('enquiry', 'activity_type', 'performed_by', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('enquiry__reference_id', 'title', 'description')

