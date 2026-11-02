import os
import hashlib
from django.db import models
from django.utils import timezone
from django.conf import settings
from requirements.models import ProjectRequirement


class AssetCategory(models.TextChoices):
    PRIMARY_LOGO = 'PRIMARY_LOGO', 'Primary Brand Logo'
    SECONDARY_LOGO = 'SECONDARY_LOGO', 'Secondary Logo'
    LOGO_VARIATION = 'LOGO_VARIATION', 'Logo Variation'
    BRAND_ICON = 'BRAND_ICON', 'Brand Icon'
    FAVICON = 'FAVICON', 'Favicon'
    COLOR_PALETTE = 'COLOR_PALETTE', 'Brand Colour Palette'
    TYPOGRAPHY = 'TYPOGRAPHY', 'Typography / Font Reference'
    GUIDELINES_PDF = 'GUIDELINES_PDF', 'Brand Guidelines PDF'
    REFERENCE_IMAGE = 'REFERENCE_IMAGE', 'Reference Images'
    PRODUCT_IMAGE = 'PRODUCT_IMAGE', 'Product Images'
    BANNER = 'BANNER', 'Banners & Posters'
    MARKETING_ASSET = 'MARKETING_ASSET', 'Marketing Assets'
    UI_SCREENSHOT = 'UI_SCREENSHOT', 'UI Reference Screenshots'
    WIREFRAME = 'WIREFRAME', 'Wireframes / Design Files'
    EXISTING_SITE_SCREENSHOT = 'EXISTING_SITE_SCREENSHOT', 'Existing Website Screenshots'
    TECHNICAL_SPEC = 'TECHNICAL_SPEC', 'Technical Specifications / API Docs'
    PROPOSAL_DOC = 'PROPOSAL_DOC', 'Approved Proposal'
    SIGNED_REQUIREMENTS = 'SIGNED_REQUIREMENTS', 'Signed-off Requirements'
    OTHER_ATTACHMENT = 'OTHER_ATTACHMENT', 'Other Project Attachment'


class AssetStatus(models.TextChoices):
    REQUIRED = 'REQUIRED', 'Required Asset'
    REQUESTED = 'REQUESTED', 'Requested from Client'
    RECEIVED = 'RECEIVED', 'Received'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    REPLACEMENT_REQUIRED = 'REPLACEMENT_REQUIRED', 'Replacement Required'


def asset_upload_path(instance, filename):
    req_ref = instance.requirement.requirement_reference if instance.requirement else 'general'
    safe_name = os.path.basename(filename).replace(' ', '_')
    return f"private_assets/{req_ref}/{instance.category.lower()}/{safe_name}"


class ClientBrandAsset(models.Model):
    requirement = models.ForeignKey(
        ProjectRequirement,
        on_delete=models.CASCADE,
        related_name='brand_assets'
    )
    title = models.CharField(max_length=200)
    category = models.CharField(
        max_length=40,
        choices=AssetCategory.choices,
        default=AssetCategory.PRIMARY_LOGO,
        db_index=True
    )
    file = models.FileField(upload_to=asset_upload_path, blank=True, null=True)
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, blank=True, default='')
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    checksum_sha256 = models.CharField(max_length=64, blank=True, default='')

    status = models.CharField(
        max_length=30,
        choices=AssetStatus.choices,
        default=AssetStatus.RECEIVED,
        db_index=True
    )
    version = models.PositiveIntegerField(default=1)
    is_latest = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, default='')

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_assets'
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['category', '-version', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_category_display()}) - V{self.version} [{self.get_status_display()}]"

    def compute_checksum(self):
        if self.file and os.path.exists(self.file.path):
            hasher = hashlib.sha256()
            with open(self.file.path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    hasher.update(chunk)
            self.checksum_sha256 = hasher.hexdigest()
            self.file_size = os.path.getsize(self.file.path)
            return self.checksum_sha256
        return ''
