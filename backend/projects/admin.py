from django.contrib import admin
from .models import DeveloperProject, ProjectMilestone, ProjectDeliverable


class ProjectMilestoneInline(admin.TabularInline):
    model = ProjectMilestone
    extra = 0


class ProjectDeliverableInline(admin.TabularInline):
    model = ProjectDeliverable
    extra = 0


@admin.register(DeveloperProject)
class DeveloperProjectAdmin(admin.ModelAdmin):
    list_display = ('project_code', 'title', 'assigned_developer', 'status', 'progress_percentage', 'expected_completion_date', 'updated_at')
    list_filter = ('status', 'expected_completion_date')
    search_fields = ('project_code', 'title', 'assigned_developer__username')
    inlines = [ProjectMilestoneInline, ProjectDeliverableInline]


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'completed', 'completed_at', 'due_date')
    list_filter = ('completed', 'due_date')
    search_fields = ('title', 'project__title', 'project__project_code')


@admin.register(ProjectDeliverable)
class ProjectDeliverableAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'deliverable_type', 'uploaded_by', 'uploaded_at', 'status')
    list_filter = ('deliverable_type', 'status', 'uploaded_at')
    search_fields = ('title', 'project__title', 'project__project_code')

