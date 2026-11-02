import os
import io
import json
import csv
import zipfile
import hashlib
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from .models import HandoverRecord
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def compute_sha256(data_bytes):
    return hashlib.sha256(data_bytes).hexdigest()


def generate_pdf_summary(title, sections, output_path):
    """Generate a clean branded PDF summary using ReportLab."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#07132e'),
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1465f4'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#101c36')
    )

    story = []
    story.append(Paragraph(f"<b>XEYR TECHNOLOGIES PRIVATE LIMITED</b>", title_style))
    story.append(Paragraph(f"<b>{title}</b>", h2_style))
    story.append(Paragraph(f"Generated at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Confidential Developer Handover", body_style))
    story.append(Spacer(1, 15))

    for sec_title, sec_content in sections:
        story.append(Paragraph(f"<b>{sec_title}</b>", h2_style))
        if isinstance(sec_content, list):
            for item in sec_content:
                story.append(Paragraph(f"• {item}", body_style))
        else:
            story.append(Paragraph(str(sec_content).replace('\n', '<br/>'), body_style))
        story.append(Spacer(1, 10))

    doc.build(story)


class HandoverZipGenerator:
    """
    Automated Developer Handover ZIP Generator for XEYR Technologies.
    Generates structured, validated project packages with checksums and manifests.
    """

    def __init__(self, requirement, user, exception_notes=""):
        self.requirement = requirement
        self.enquiry = requirement.enquiry
        self.user = user
        self.exception_notes = exception_notes
        self.manifest_entries = []
        self.asset_inventory = []

    def validate_readiness(self):
        """Check all readiness criteria before generating handover."""
        assets = self.requirement.brand_assets.filter(is_latest=True)
        checks = {
            "enquiry_qualified": self.enquiry.status in ['QUALIFIED', 'REQUIREMENTS_PENDING', 'REQUIREMENTS_COMPLETED', 'AWAITING_CLIENT_APPROVAL', 'READY_FOR_HANDOVER', 'PROJECT_CREATED'],
            "client_info_verified": bool(self.requirement.legal_business_name or self.enquiry.client_name),
            "requirements_completed": bool(self.requirement.project_name and (self.requirement.scope_of_work or self.requirement.functional_requirements)),
            "scope_documented": bool(self.requirement.scope_of_work),
            "technical_reqs_documented": bool(self.requirement.preferred_framework or self.requirement.backend_requirements or self.requirement.database_requirements),
            "acceptance_criteria_defined": bool(self.requirement.acceptance_criteria or self.requirement.delivery_checklist),
            "commercial_approved": bool(self.requirement.approved_budget > 0 or self.requirement.commercial_approval_status in ['Approved', 'Confirmed']),
            "has_brand_assets": assets.filter(status='APPROVED').exists() or assets.exists(),
        }
        all_passed = all(checks.values())
        return checks, all_passed

    def generate(self, force_with_exception=False):
        checks, all_passed = self.validate_readiness()

        if not all_passed and not force_with_exception:
            missing = [k for k, v in checks.items() if not v]
            raise ValueError(f"Handover readiness validation failed. Incomplete items: {', '.join(missing)}")

        req = self.requirement
        enq = self.enquiry
        project_ref = req.requirement_reference
        folder_prefix = f"XEYR_Project_Handover_{project_ref}"

        # Determine version
        existing_count = req.handover_records.count()
        version = existing_count + 1
        handover_ref = f"XEYR-HO-{timezone.now().year}-{project_ref.split('-')[-1]}-V{version}"

        # Prepare archive output path
        archive_dir = os.path.join(settings.HANDOVER_ROOT, project_ref)
        os.makedirs(archive_dir, exist_ok=True)
        zip_filename = f"{folder_prefix}_V{version}.zip"
        zip_filepath = os.path.join(archive_dir, zip_filename)

        temp_dir = os.path.join(archive_dir, f"temp_{version}")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:

                SENSITIVE_PATTERNS = {'.env', '.env.local', '.env.production', 'secrets.json', 'credentials.json', 'id_rsa', 'id_dsa', 'id_ed25519'}
                SENSITIVE_EXTS = {'.sql', '.dump', '.key', '.pem', '.cer', '.crt', '.p12', '.pfx'}

                def add_file_to_zip(rel_path, content_bytes):
                    # Prevent path traversal
                    clean_path = os.path.normpath(rel_path).replace('\\', '/')
                    if clean_path.startswith('/') or '..' in clean_path.split('/'):
                        raise ValueError(f"Unsafe file path: {rel_path}")

                    # Prevent leakage of credentials, .env files, database dumps or private keys
                    basename = os.path.basename(clean_path).lower()
                    ext = os.path.splitext(basename)[1].lower()
                    if basename in SENSITIVE_PATTERNS or ext in SENSITIVE_EXTS or 'password' in basename:
                        return None  # Exclude sensitive file safely

                    full_zip_path = f"{folder_prefix}/{clean_path}"
                    zf.writestr(full_zip_path, content_bytes)
                    sha256 = compute_sha256(content_bytes)
                    self.manifest_entries.append({
                        "file_path": clean_path,
                        "file_size": len(content_bytes),
                        "sha256": sha256
                    })
                    return sha256

                # 1. README.md
                readme_content = f"""# {req.project_name} - Developer Handover Package
## XEYR Technologies Private Limited
- **Handover Reference:** {handover_ref}
- **Project Reference:** {project_ref}
- **Enquiry Reference:** {enq.reference_id}
- **Handover Version:** V{version}
- **Generated Date:** {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Generated By:** {self.user.get_full_name() or self.user.username} ({self.user.get_role_display()})

### Handover Instructions
1. Review `PROJECT_SUMMARY.md` and `REQUIREMENTS/requirements_summary.md` thoroughly before development.
2. Verify all deliverables against `REQUIREMENTS/scope_and_deliverables.json`.
3. Adhere strictly to the brand standards in `BRAND_ASSETS/` and design references in `DESIGN_REFERENCES/`.
4. Ensure all database models, APIs, and security controls conform to `TECHNICAL_DOCUMENTATION/architecture_requirements.md`.
5. Strictly avoid committing any secrets, API keys, credentials, or private keys to source control.
"""
                add_file_to_zip("README.md", readme_content.encode('utf-8'))

                # 2. PROJECT_SUMMARY.md
                summary_content = f"""# Project Summary: {req.project_name}

### Client & Business Overview
- **Client Organization:** {req.legal_business_name or enq.client_name}
- **Contact Person:** {req.client_contact_person or enq.contact_person}
- **Official Email:** {req.official_email or enq.email}
- **Industry:** {req.industry_category or enq.organisation_type}
- **Project Type:** {req.project_type}

### Business Challenge & Problem Statement
{req.business_problem or 'As specified in enquiry and qualification notes.'}

### Project Goals & Target Audience
- **Goals:** {req.project_goals or 'Deliver high-performance, robust software solution.'}
- **Target Audience:** {req.target_audience or 'General public and authorized business users.'}

### Scope & Priority
- **Priority:** {req.priority}
- **Expected Delivery Date:** {req.expected_delivery_date.strftime('%Y-%m-%d') if req.expected_delivery_date else 'To be scheduled'}
- **Deliverables:**
{chr(10).join(f"- {d}" for d in (req.expected_deliverables if isinstance(req.expected_deliverables, list) else [req.expected_deliverables]))}
"""
                add_file_to_zip("PROJECT_SUMMARY.md", summary_content.encode('utf-8'))

                # 3. CLIENT_INFORMATION/client_profile.json
                client_info = {
                    "legal_name": req.legal_business_name or enq.client_name,
                    "contact_person": req.client_contact_person or enq.contact_person,
                    "official_email": req.official_email or enq.email,
                    "official_phone": req.official_phone or enq.phone,
                    "business_address": req.business_address,
                    "industry": req.industry_category or enq.organisation_type,
                    "websites_and_socials": req.website_and_socials,
                    "enquiry_source": enq.source,
                    "enquiry_date": enq.created_at.isoformat()
                }
                add_file_to_zip("CLIENT_INFORMATION/client_profile.json", json.dumps(client_info, indent=2).encode('utf-8'))

                # 4. REQUIREMENTS/
                # Generate PDF summary
                pdf_path = os.path.join(temp_dir, "requirements_summary.pdf")
                pdf_sections = [
                    ("Client Overview", f"Client: {req.legal_business_name or enq.client_name}\nProject: {req.project_name}\nType: {req.project_type}"),
                    ("Scope of Work", req.scope_of_work or "Refer to technical requirements."),
                    ("Functional Requirements", req.functional_requirements or "Refer to functional specs."),
                    ("Technical Specifications", f"Stack: {req.preferred_framework}\nDatabase: {req.database_requirements}\nDeployment: {req.deployment_platform}"),
                    ("Deliverables", req.expected_deliverables if isinstance(req.expected_deliverables, list) else [str(req.expected_deliverables)]),
                    ("Acceptance Criteria", req.acceptance_criteria or "Deliverable must pass all automated tests and client approval."),
                ]
                generate_pdf_summary(f"Project Requirements: {req.project_name}", pdf_sections, pdf_path)
                with open(pdf_path, 'rb') as f:
                    add_file_to_zip("REQUIREMENTS/requirements_summary.pdf", f.read())

                # requirements_summary.md
                req_md = f"""# Detailed Requirements: {req.project_name}

## 1. Functional Requirements
{req.functional_requirements or 'Detailed in functional_requirements.json'}

## 2. Technical Stack & Preferences
- **Framework:** {req.preferred_framework}
- **Backend:** {req.backend_requirements}
- **Database:** {req.database_requirements}
- **Integrations:** {req.api_integrations}
- **Deployment Platform:** {req.deployment_platform}

## 3. Scope of Work
{req.scope_of_work}

## 4. Acceptance Criteria
{req.acceptance_criteria or 'All features must satisfy functional specs and pass QA verification.'}
"""
                add_file_to_zip("REQUIREMENTS/requirements_summary.md", req_md.encode('utf-8'))

                # JSON Requirements files
                func_reqs = {
                    "project_name": req.project_name,
                    "scope_of_work": req.scope_of_work,
                    "features_required": req.features_required,
                    "functional_requirements": req.functional_requirements,
                    "non_functional_requirements": req.non_functional_requirements,
                    "accessibility_requirements": req.accessibility_responsive_reqs,
                    "maintenance_requirements": req.maintenance_reqs
                }
                add_file_to_zip("REQUIREMENTS/functional_requirements.json", json.dumps(func_reqs, indent=2).encode('utf-8'))

                tech_reqs = {
                    "preferred_framework": req.preferred_framework,
                    "backend": req.backend_requirements,
                    "database": req.database_requirements,
                    "api_integrations": req.api_integrations,
                    "authentication": req.auth_requirements,
                    "user_roles": req.user_roles_req,
                    "security": req.security_requirements,
                    "deployment_platform": req.deployment_platform,
                    "repository": req.repository_details,
                    "testing": req.testing_requirements
                }
                add_file_to_zip("REQUIREMENTS/technical_requirements.json", json.dumps(tech_reqs, indent=2).encode('utf-8'))

                design_reqs = {
                    "design_style": req.design_style,
                    "color_preferences": req.color_preferences,
                    "typography_preferences": req.typography_preferences,
                    "ui_ux_requirements": req.ui_ux_requirements,
                    "brand_guidelines": req.brand_guidelines_notes,
                    "required_pages": req.required_page_list,
                    "devices": req.device_requirements
                }
                add_file_to_zip("REQUIREMENTS/design_requirements.json", json.dumps(design_reqs, indent=2).encode('utf-8'))

                scope_deliv = {
                    "deliverables": req.expected_deliverables,
                    "scope_of_work": req.scope_of_work,
                    "hosting_deployment": req.hosting_deployment_reqs
                }
                add_file_to_zip("REQUIREMENTS/scope_and_deliverables.json", json.dumps(scope_deliv, indent=2).encode('utf-8'))

                accept_crit = {
                    "criteria": req.acceptance_criteria,
                    "delivery_checklist": req.delivery_checklist
                }
                add_file_to_zip("REQUIREMENTS/acceptance_criteria.json", json.dumps(accept_crit, indent=2).encode('utf-8'))

                # 5. BRAND_ASSETS/ & DESIGN_REFERENCES/
                # Include actual uploaded files
                assets = req.brand_assets.filter(is_latest=True)
                seen_names = set()

                for asset in assets:
                    cat = asset.category
                    orig_filename = asset.filename or (os.path.basename(asset.file.name) if asset.file else f"asset_{asset.id}")
                    safe_filename = os.path.basename(orig_filename)

                    # Deduplicate filenames safely
                    base, ext = os.path.splitext(safe_filename)
                    counter = 1
                    while safe_filename in seen_names:
                        safe_filename = f"{base}_{counter}{ext}"
                        counter += 1
                    seen_names.add(safe_filename)

                    # Map category to directory
                    if cat in ['PRIMARY_LOGO', 'SECONDARY_LOGO', 'LOGO_VARIATION']:
                        dest_sub = "BRAND_ASSETS/logos"
                    elif cat in ['BRAND_ICON', 'FAVICON']:
                        dest_sub = "BRAND_ASSETS/icons"
                    elif cat in ['GUIDELINES_PDF', 'COLOR_PALETTE', 'TYPOGRAPHY']:
                        dest_sub = "BRAND_ASSETS/brand_guidelines"
                    elif cat in ['REFERENCE_IMAGE', 'PRODUCT_IMAGE', 'BANNER', 'MARKETING_ASSET']:
                        dest_sub = "BRAND_ASSETS/reference_images"
                    elif cat in ['UI_SCREENSHOT', 'EXISTING_SITE_SCREENSHOT']:
                        dest_sub = "DESIGN_REFERENCES/screenshots"
                    elif cat in ['WIREFRAME']:
                        dest_sub = "DESIGN_REFERENCES/wireframes"
                    else:
                        dest_sub = "TECHNICAL_DOCUMENTATION"

                    file_data = b""
                    if asset.file and os.path.exists(asset.file.path):
                        with open(asset.file.path, 'rb') as af:
                            file_data = af.read()
                    else:
                        # Placeholder text note if physical file absent
                        file_data = f"# Asset Record: {asset.title}\nCategory: {asset.get_category_display()}\nStatus: {asset.get_status_display()}\nNotes: {asset.notes}".encode('utf-8')
                        safe_filename = f"{base}_info.txt"

                    dest_path = f"{dest_sub}/{safe_filename}"
                    sha = add_file_to_zip(dest_path, file_data)

                    self.asset_inventory.append({
                        "category": asset.get_category_display(),
                        "title": asset.title,
                        "filename": safe_filename,
                        "size_bytes": len(file_data),
                        "sha256": sha,
                        "status": asset.get_status_display()
                    })

                # Reference links markdown
                ref_links_md = f"""# Design References & Links
- **Reference Websites:**
{req.reference_websites or 'None provided.'}
- **Wireframe Notes:**
{req.wireframe_notes or 'None provided.'}
"""
                add_file_to_zip("DESIGN_REFERENCES/reference_links.md", ref_links_md.encode('utf-8'))

                # 6. TECHNICAL_DOCUMENTATION/
                arch_md = f"""# Architecture Requirements
## {req.project_name}

- **Core Technologies:** {req.preferred_framework}
- **Database:** {req.database_requirements}
- **Security & Authorization:** {req.security_requirements}
- **Role Permissions:** {req.user_roles_req or 'Standard Role-Based Access Control'}

### Security Guidelines for Developers
1. Never commit `.env` or credentials into version control.
2. Enforce CSRF protection and rate limiting on all public endpoints.
3. Validate and sanitize all user input server-side.
4. Restrict confidential assets to authenticated, authorized users.
"""
                add_file_to_zip("TECHNICAL_DOCUMENTATION/architecture_requirements.md", arch_md.encode('utf-8'))

                integrations_json = {
                    "integrations_required": req.integrations_required,
                    "auth_requirements": req.auth_requirements,
                    "database": req.database_requirements
                }
                add_file_to_zip("TECHNICAL_DOCUMENTATION/integrations.json", json.dumps(integrations_json, indent=2).encode('utf-8'))

                deploy_md = f"""# Deployment Requirements
- **Platform:** {req.deployment_platform or 'Linux VPS / Containerized environment'}
- **Hosting / Domain Setup:** {req.hosting_deployment_reqs or 'Standard HTTPS / NGINX reverse proxy'}
- **Database:** {req.database_requirements}
"""
                add_file_to_zip("TECHNICAL_DOCUMENTATION/deployment_requirements.md", deploy_md.encode('utf-8'))

                test_md = f"""# Testing & QA Requirements
- **Testing Standard:** {req.testing_requirements or 'Unit tests for models/services, integration tests for API endpoints'}
- **Coverage Goal:** At least 80% coverage on critical business workflows.
"""
                add_file_to_zip("TECHNICAL_DOCUMENTATION/testing_requirements.md", test_md.encode('utf-8'))

                # 7. PROJECT_MANAGEMENT/
                milestones_json = req.milestones or [
                    {"name": "Sprint 1: Architecture & Data Modeling", "status": "Pending"},
                    {"name": "Sprint 2: Core Feature Implementation", "status": "Pending"},
                    {"name": "Sprint 3: QA, Client Review & Deployment", "status": "Pending"},
                ]
                add_file_to_zip("PROJECT_MANAGEMENT/milestones.json", json.dumps(milestones_json, indent=2).encode('utf-8'))

                # task_checklist.csv
                csv_buf = io.StringIO()
                cw = csv.writer(csv_buf)
                cw.writerow(["Task ID", "Task Title", "Priority", "Status", "Owner"])
                if isinstance(req.tasks, list) and req.tasks:
                    for idx, t in enumerate(req.tasks, 1):
                        title = t.get('title', str(t)) if isinstance(t, dict) else str(t)
                        cw.writerow([f"TASK-{idx:03d}", title, req.priority, "Pending", req.developer_assigned.username if req.developer_assigned else "Unassigned"])
                else:
                    cw.writerow(["TASK-001", "Initialize Repository and Environment", "High", "Pending", "Lead Dev"])
                    cw.writerow(["TASK-002", "Implement Database Models & Migrations", "High", "Pending", "Backend Dev"])
                    cw.writerow(["TASK-003", "Build API Endpoints with Validation", "High", "Pending", "Backend Dev"])
                    cw.writerow(["TASK-004", "Frontend UI Integration", "Medium", "Pending", "Frontend Dev"])
                    cw.writerow(["TASK-005", "Automated QA & Delivery Verification", "High", "Pending", "QA / Dev"])
                add_file_to_zip("PROJECT_MANAGEMENT/task_checklist.csv", csv_buf.getvalue().encode('utf-8'))

                delivery_checklist_md = f"""# Delivery Checklist
- [ ] Core functional requirements developed and tested
- [ ] Database migrations executed without errors
- [ ] API validation and error handling verified
- [ ] Responsive design verified on desktop, tablet, and mobile
- [ ] Security audit: No secrets committed, CSRF active, permissions checked
- [ ] Acceptance criteria verified: {req.acceptance_criteria or 'Satisfied'}
"""
                add_file_to_zip("PROJECT_MANAGEMENT/delivery_checklist.md", delivery_checklist_md.encode('utf-8'))

                risks_json = req.risks or [
                    {"risk": "Scope Creep", "mitigation": "Strict adherence to approved scope_and_deliverables.json"},
                    {"risk": "Third-party API downtime", "mitigation": "Graceful fallback and retry mechanisms"}
                ]
                add_file_to_zip("PROJECT_MANAGEMENT/risk_register.json", json.dumps(risks_json, indent=2).encode('utf-8'))

                # 8. COMMERCIAL_SUMMARY/
                comm_pdf_path = os.path.join(temp_dir, "approved_commercial_summary.pdf")
                comm_sections = [
                    ("Approved Scope", f"Project: {req.project_name}\nContract Reference: {req.contract_proposal_ref or 'Direct Approval'}"),
                    ("Commercial Approval Status", f"Status: {req.commercial_approval_status}\nApproved Budget: INR {req.approved_budget:,.2f}"),
                    ("Payment Milestones", [f"{m.get('title', 'Milestone')}: INR {m.get('amount', 0)}" for m in req.payment_milestones] if req.payment_milestones else ["Payment terms as per mutual agreement."]),
                    ("Delivery Timeline", f"Expected Start: {req.expected_start_date or 'Immediate'}\nExpected Delivery: {req.expected_delivery_date or 'To be agreed'}"),
                ]
                generate_pdf_summary(f"Approved Commercial Summary: {req.project_name}", comm_sections, comm_pdf_path)
                with open(comm_pdf_path, 'rb') as f:
                    add_file_to_zip("COMMERCIAL_SUMMARY/approved_commercial_summary.pdf", f.read())

                # 9. HANDOVER_METADATA/
                # asset_inventory.csv
                inv_buf = io.StringIO()
                iw = csv.writer(inv_buf)
                iw.writerow(["Category", "Title", "Filename", "SizeBytes", "SHA256", "Status"])
                for item in self.asset_inventory:
                    iw.writerow([item["category"], item["title"], item["filename"], item["size_bytes"], item["sha256"], item["status"]])
                add_file_to_zip("HANDOVER_METADATA/asset_inventory.csv", inv_buf.getvalue().encode('utf-8'))

                # manifest.json
                manifest_data = {
                    "handover_reference": handover_ref,
                    "project_reference": project_ref,
                    "project_name": req.project_name,
                    "version": version,
                    "generated_at": timezone.now().isoformat(),
                    "generated_by": {
                        "username": self.user.username,
                        "full_name": self.user.get_full_name(),
                        "role": self.user.role
                    },
                    "total_files": len(self.manifest_entries) + 1,  # including manifest itself
                    "files": self.manifest_entries
                }
                # write manifest.json
                zf.writestr(f"{folder_prefix}/HANDOVER_METADATA/manifest.json", json.dumps(manifest_data, indent=2).encode('utf-8'))

        finally:
            # Clean up temporary directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

        # Compute ZIP file size and hash
        zip_size = os.path.getsize(zip_filepath)
        with open(zip_filepath, 'rb') as f:
            zip_sha = compute_sha256(f.read())

        # Save HandoverRecord in PostgreSQL
        record = HandoverRecord.objects.create(
            requirement=req,
            handover_reference=handover_ref,
            version=version,
            zip_file=f"handover_archives/{project_ref}/{zip_filename}",
            zip_filename=zip_filename,
            zip_size=zip_size,
            zip_checksum_sha256=zip_sha,
            manifest_data=manifest_data,
            readiness_checklist=checks,
            all_checks_passed=all_passed,
            has_documented_exception=bool(self.exception_notes),
            exception_notes=self.exception_notes,
            generated_by=self.user,
            assigned_developer=req.developer_assigned,
            priority=req.priority,
            expected_delivery_date=req.expected_delivery_date
        )

        # Update requirement status to READY_FOR_HANDOVER if approved
        if req.status != 'READY_FOR_HANDOVER':
            req.status = 'READY_FOR_HANDOVER'
            req.save(update_fields=['status'])

        return record
