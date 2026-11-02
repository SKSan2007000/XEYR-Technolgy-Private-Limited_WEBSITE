from rest_framework import serializers
from .models import ClientBrandAsset, AssetCategory, AssetStatus


class ClientBrandAssetSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = ClientBrandAsset
        fields = [
            'id', 'requirement', 'title', 'category', 'category_display',
            'file', 'filename', 'file_type', 'file_size', 'checksum_sha256',
            'status', 'status_display', 'version', 'is_latest', 'notes',
            'uploaded_by', 'uploaded_by_name', 'created_at', 'download_url'
        ]
        read_only_fields = ['id', 'uploaded_by', 'created_at', 'checksum_sha256', 'file_size']

    def get_download_url(self, obj):
        return f"/api/assets/{obj.id}/download/"


class AssetChecklistSerializer(serializers.Serializer):
    category = serializers.CharField()
    label = serializers.CharField()
    is_received = serializers.BooleanField()
    is_approved = serializers.BooleanField()
    asset_id = serializers.IntegerField(allow_null=True)
    filename = serializers.CharField(allow_null=True)
    status = serializers.CharField(allow_null=True)
