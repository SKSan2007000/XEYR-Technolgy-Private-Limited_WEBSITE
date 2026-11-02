from django.contrib import admin
from .models import ClientBrandAsset


@admin.register(ClientBrandAsset)
class ClientBrandAssetAdmin(admin.ModelAdmin):
    list_display = ('title', 'requirement', 'category', 'status', 'file_size', 'checksum_sha256', 'uploaded_by', 'created_at')
    list_filter = ('category', 'status', 'created_at')
    search_fields = ('title', 'requirement__requirement_reference', 'checksum_sha256')
    readonly_fields = ('checksum_sha256', 'file_size', 'created_at')

