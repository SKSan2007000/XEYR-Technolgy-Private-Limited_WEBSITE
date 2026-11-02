from django.contrib import admin
from .models import ProjectRequirement


@admin.register(ProjectRequirement)
class ProjectRequirementAdmin(admin.ModelAdmin):
    list_display = ('requirement_reference', 'project_name', 'enquiry', 'status', 'version', 'approved_budget', 'updated_at')
    list_filter = ('status', 'preferred_framework', 'database_requirements', 'created_at')
    search_fields = ('requirement_reference', 'project_name', 'legal_business_name', 'scope_of_work')
    readonly_fields = ('requirement_reference', 'version', 'created_at', 'updated_at')

