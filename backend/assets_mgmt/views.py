import os
from django.http import FileResponse, Http404
from django.db import transaction
from django.conf import settings
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ClientBrandAsset, AssetCategory, AssetStatus
from .serializers import ClientBrandAssetSerializer
from requirements.models import ProjectRequirement
from core.models import AuditLog


BLOCKED_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.sh', '.vbs', '.js', '.msi', '.com', '.scr', '.pif',
    '.py', '.php', '.php3', '.php4', '.php5', '.phtml', '.jsp', '.asp', '.aspx',
    '.cgi', '.pl', '.jar', '.war', '.shtml', '.htaccess', '.env', '.config'
}


class AssetListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, requirement_id=None):
        assets = ClientBrandAsset.objects.select_related('requirement', 'uploaded_by')
        if requirement_id:
            assets = assets.filter(requirement_id=requirement_id)
        category = request.query_params.get('category')
        if category:
            assets = assets.filter(category=category)
        serializer = ClientBrandAssetSerializer(assets, many=True)
        return Response(serializer.data)

    def post(self, request, requirement_id=None):
        req_id = requirement_id or request.data.get('requirement_id') or request.data.get('requirement')
        if not req_id:
            return Response({'error': 'Project requirement ID is required for asset upload.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            req = ProjectRequirement.objects.get(pk=req_id)
        except ProjectRequirement.DoesNotExist:
            return Response({'error': 'Requirement workspace not found.'}, status=status.HTTP_404_NOT_FOUND)

        uploaded_file = request.FILES.get('file')
        title = request.data.get('title')
        category = request.data.get('category', AssetCategory.PRIMARY_LOGO)
        notes = request.data.get('notes', '')

        if not uploaded_file and not title:
            return Response({'error': 'File or asset title is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file safety
        if uploaded_file:
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext in BLOCKED_EXTENSIONS:
                return Response({'error': f'Unsafe file type {ext} is blocked for security.'}, status=status.HTTP_400_BAD_REQUEST)

            if uploaded_file.size > 52428800:
                return Response({'error': 'File exceeds maximum upload size of 50 MB.'}, status=status.HTTP_400_BAD_REQUEST)

        # Handle versioning if asset in category already exists
        with transaction.atomic():
            existing = ClientBrandAsset.objects.filter(requirement=req, category=category, is_latest=True).first()
            version = 1
            if existing and request.data.get('replace', 'false').lower() in ['true', '1']:
                existing.is_latest = False
                existing.save(update_fields=['is_latest'])
                version = existing.version + 1

            filename = uploaded_file.name if uploaded_file else f"{title}.asset"
            file_type = uploaded_file.content_type if uploaded_file else 'application/octet-stream'

            asset = ClientBrandAsset.objects.create(
                requirement=req,
                title=title or filename,
                category=category,
                file=uploaded_file,
                filename=filename,
                file_type=file_type,
                status=AssetStatus.RECEIVED if uploaded_file else AssetStatus.REQUESTED,
                version=version,
                is_latest=True,
                notes=notes,
                uploaded_by=request.user
            )

            # Compute SHA-256 and size
            asset.compute_checksum()
            asset.save(update_fields=['checksum_sha256', 'file_size'])

            AuditLog.log('ASSET_UPLOADED', 'ClientBrandAsset', asset.id, user=request.user, details={'filename': filename, 'category': category, 'version': version}, request=request)

        return Response(ClientBrandAssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class AssetDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            asset = ClientBrandAsset.objects.get(pk=pk)
        except ClientBrandAsset.DoesNotExist:
            return Response({'error': 'Asset not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ClientBrandAssetSerializer(asset).data)

    def patch(self, request, pk):
        try:
            asset = ClientBrandAsset.objects.get(pk=pk)
        except ClientBrandAsset.DoesNotExist:
            return Response({'error': 'Asset not found.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        notes = request.data.get('notes')

        if new_status and new_status in AssetStatus.values:
            asset.status = new_status
        if notes is not None:
            asset.notes = notes
        asset.save()

        AuditLog.log('ASSET_STATUS_UPDATED', 'ClientBrandAsset', asset.id, user=request.user, details={'status': asset.status}, request=request)
        return Response(ClientBrandAssetSerializer(asset).data)

    def delete(self, request, pk):
        try:
            asset = ClientBrandAsset.objects.get(pk=pk)
        except ClientBrandAsset.DoesNotExist:
            return Response({'error': 'Asset not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'BUSINESS_ADMIN']):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        AuditLog.log('ASSET_DELETED', 'ClientBrandAsset', asset.id, user=request.user, details={'filename': asset.filename}, request=request)
        asset.delete()
        return Response({'message': 'Asset removed successfully.'})


class AssetSecureDownloadView(APIView):
    """
    Private, authenticated download endpoint.
    Verifies user permissions before streaming private assets.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            asset = ClientBrandAsset.objects.select_related('requirement').get(pk=pk)
        except ClientBrandAsset.DoesNotExist:
            raise Http404("Asset not found.")

        # Check permissions: Devs can only access their assigned projects
        if request.user.role == 'DEVELOPER':
            is_assigned = (
                asset.requirement.developer_assigned == request.user or
                hasattr(asset.requirement, 'developer_project') and asset.requirement.developer_project.assigned_developer == request.user
            )
            if not is_assigned:
                return Response({'error': 'You are only authorized to access assets for your assigned projects.'}, status=status.HTTP_403_FORBIDDEN)

        if not asset.file or not os.path.exists(asset.file.path):
            raise Http404("Asset file not available on disk.")

        AuditLog.log('ASSET_DOWNLOADED', 'ClientBrandAsset', asset.id, user=request.user, details={'filename': asset.filename}, request=request)
        return FileResponse(open(asset.file.path, 'rb'), as_attachment=True, filename=asset.filename)


class AssetChecklistView(APIView):
    """
    Returns brand assets completeness checklist for a requirement.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, requirement_id):
        try:
            req = ProjectRequirement.objects.get(pk=requirement_id)
        except ProjectRequirement.DoesNotExist:
            return Response({'error': 'Requirement workspace not found.'}, status=status.HTTP_404_NOT_FOUND)

        assets = req.brand_assets.filter(is_latest=True)

        categories_to_check = [
            (AssetCategory.PRIMARY_LOGO, "Primary Brand Logo"),
            (AssetCategory.SECONDARY_LOGO, "Secondary Logo"),
            (AssetCategory.FAVICON, "Favicon / Brand Icon"),
            (AssetCategory.COLOR_PALETTE, "Brand Colour Palette"),
            (AssetCategory.TYPOGRAPHY, "Typography / Font Reference"),
            (AssetCategory.GUIDELINES_PDF, "Brand Guidelines Document"),
            (AssetCategory.UI_SCREENSHOT, "UI Reference Screenshots"),
            (AssetCategory.WIREFRAME, "Wireframes / Architecture"),
        ]

        checklist = []
        for cat_key, cat_label in categories_to_check:
            matched = assets.filter(category=cat_key).first()
            checklist.append({
                'category': cat_key,
                'label': cat_label,
                'is_received': bool(matched and matched.status in ['RECEIVED', 'APPROVED']),
                'is_approved': bool(matched and matched.status == 'APPROVED'),
                'asset_id': matched.id if matched else None,
                'filename': matched.filename if matched else None,
                'status': matched.get_status_display() if matched else 'Not Provided'
            })

        return Response({
            'requirement_reference': req.requirement_reference,
            'checklist': checklist,
            'total_items': len(checklist),
            'received_count': sum(1 for c in checklist if c['is_received']),
            'approved_count': sum(1 for c in checklist if c['is_approved'])
        })
