import os
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, UserRole, AuditLog, Notification
from crm.models import Enquiry, EnquiryStatus, EnquiryQualification, EnquiryRejection, RejectionCategory, CRMActivity
from requirements.models import ProjectRequirement, RequirementStatus
from assets_mgmt.models import ClientBrandAsset, AssetCategory, AssetStatus
from handover.models import HandoverRecord
from handover.generator import HandoverZipGenerator
from projects.models import DeveloperProject, ProjectStatus, ProjectMilestone
from finance.models import InvoiceQuote, PaymentRecord, ExpenseRecord
from events_mgmt.models import (
    EventListing, EventRegistration, EventFormField,
    SocialMediaConfig, EventNotificationSubscriber
)


class Command(BaseCommand):
    help = 'Seeds initial administrative accounts and foundational business data for XEYR OS'

    def handle(self, *args, **options):
        self.stdout.write("Seeding XEYR Business OS database...")

        # 1. Create Default Users
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@xeyr.in',
                'first_name': 'Santhosh',
                'last_name': 'Kumar',
                'role': UserRole.SUPER_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'phone': '+91 80562 53897',
                'department': 'Executive Leadership'
            }
        )
        admin_user.set_password('XeyrAdmin@2026')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        sales_user, _ = User.objects.get_or_create(
            username='sales_lead',
            defaults={
                'email': 'sales@xeyr.in',
                'first_name': 'Kavitha',
                'last_name': 'Rajan',
                'role': UserRole.SALES_CRM,
                'phone': '+91 98401 23456',
                'department': 'Business Development'
            }
        )
        sales_user.set_password('XeyrStaff@2026')
        sales_user.save()

        dev_user, _ = User.objects.get_or_create(
            username='lead_dev',
            defaults={
                'email': 'developer@xeyr.in',
                'first_name': 'Arun',
                'last_name': 'Vignesh',
                'role': UserRole.DEVELOPER,
                'phone': '+91 97102 34567',
                'department': 'Core Engineering'
            }
        )
        dev_user.set_password('XeyrStaff@2026')
        dev_user.save()

        pm_user, _ = User.objects.get_or_create(
            username='project_mgr',
            defaults={
                'email': 'pm@xeyr.in',
                'first_name': 'Deepa',
                'last_name': 'Sundar',
                'role': UserRole.PROJECT_MANAGER,
                'phone': '+91 98845 67890',
                'department': 'Project Delivery'
            }
        )
        pm_user.set_password('XeyrStaff@2026')
        pm_user.save()

        self.stdout.write(self.style.SUCCESS("Users created/verified."))

        # 2. Seed Default Events & Dynamic Forms
        now = timezone.now()
        event1, _ = EventListing.objects.get_or_create(
            slug='technology-innovation-workshop',
            defaults={
                'title': 'Technology & Innovation Workshop',
                'event_type': 'Workshop',
                'status': 'UPCOMING',
                'event_date': (now + datetime.timedelta(days=7)).date(),
                'start_time': datetime.time(10, 0),
                'end_time': datetime.time(13, 0),
                'date_time': 'Upcoming Saturday, 10:00 AM IST',
                'mode': 'Hybrid (Online / Campus)',
                'venue': 'XEYR Center for Tech Excellence',
                'organizer': 'XEYR Academic & Tech Division',
                'eligibility': 'Open to all engineering students, self-taught developers, and tech enthusiasts.',
                'registration_deadline': (now + datetime.timedelta(days=6)),
                'max_participants': 120,
                'is_paid': False,
                'fee': 'Free',
                'fee_amount': 0.00,
                'currency': 'INR',
                'is_published': True,
                'description': 'Practical learning with industry-relevant ideas, tools, architecture reviews, and live demonstrations.',
                'full_description': 'Gain direct exposure to commercial engineering standards, system architecture, database design patterns, and full-stack software development workflows.',
                'contact_email': 'events@xeyr.in',
                'contact_phone': '+91 80562 53897'
            }
        )
        # Form fields for Event 1
        EventFormField.objects.get_or_create(
            event=event1, field_name='full_name',
            defaults={'field_label': 'Full Name', 'field_type': 'text', 'is_required': True, 'display_order': 1}
        )
        EventFormField.objects.get_or_create(
            event=event1, field_name='email',
            defaults={'field_label': 'Email Address', 'field_type': 'email', 'is_required': True, 'display_order': 2}
        )
        EventFormField.objects.get_or_create(
            event=event1, field_name='college_or_org',
            defaults={'field_label': 'College or Organisation', 'field_type': 'college', 'is_required': True, 'display_order': 3}
        )
        EventFormField.objects.get_or_create(
            event=event1, field_name='year_of_study',
            defaults={'field_label': 'Year of Study / Role', 'field_type': 'dropdown', 'options': '1st Year, 2nd Year, 3rd Year, Final Year, Working Professional', 'is_required': True, 'display_order': 4}
        )

        # Event 2: Paid Masterclass with Razorpay integration
        event2, _ = EventListing.objects.get_or_create(
            slug='ai-automation-masterclass',
            defaults={
                'title': 'AI & Cloud Automation Masterclass',
                'event_type': 'Masterclass',
                'status': 'UPCOMING',
                'event_date': (now + datetime.timedelta(days=14)).date(),
                'start_time': datetime.time(10, 0),
                'end_time': datetime.time(16, 0),
                'date_time': 'Next Saturday, 10:00 AM - 4:00 PM IST',
                'mode': 'Online Live Lab',
                'venue': 'Virtual Auditorium & Live Engineering Cloud Lab',
                'organizer': 'XEYR Cloud & Agentic AI Division',
                'eligibility': 'Developers, Engineers, and Final-Year Students looking to build production AI systems.',
                'registration_deadline': (now + datetime.timedelta(days=13)),
                'max_participants': 60,
                'is_paid': True,
                'fee': '₹499.00',
                'fee_amount': 499.00,
                'currency': 'INR',
                'refund_policy': '100% refund up to 24 hours prior to masterclass commencement.',
                'is_published': True,
                'description': 'Intensive hands-on masterclass building production agentic workflows, REST microservices, and automated cloud deployments.',
                'full_description': 'Deep-dive into production software engineering: designing scalable databases, implementing payment gateways, deploying AI pipelines, and generating commercial handover artifacts.',
                'contact_email': 'masterclasses@xeyr.in',
                'contact_phone': '+91 80562 53897'
            }
        )
        # Form fields for Event 2
        EventFormField.objects.get_or_create(
            event=event2, field_name='full_name',
            defaults={'field_label': 'Full Name', 'field_type': 'text', 'is_required': True, 'display_order': 1}
        )
        EventFormField.objects.get_or_create(
            event=event2, field_name='email',
            defaults={'field_label': 'Email Address', 'field_type': 'email', 'is_required': True, 'display_order': 2}
        )
        EventFormField.objects.get_or_create(
            event=event2, field_name='phone',
            defaults={'field_label': 'Phone Number (WhatsApp)', 'field_type': 'phone', 'is_required': True, 'display_order': 3}
        )
        EventFormField.objects.get_or_create(
            event=event2, field_name='primary_focus',
            defaults={'field_label': 'Primary Technical Focus', 'field_type': 'dropdown', 'options': 'Agentic AI Systems, Full-Stack Architecture, Cloud Microservices, Freelance Software Consulting', 'is_required': True, 'display_order': 4}
        )

        # Event 3: Completed Archive Event
        event3, _ = EventListing.objects.get_or_create(
            slug='full-stack-web-engineering-bootcamp',
            defaults={
                'title': 'Full-Stack Commercial Web Engineering Bootcamp',
                'event_type': 'Bootcamp',
                'status': 'COMPLETED',
                'event_date': (now - datetime.timedelta(days=35)).date(),
                'start_time': datetime.time(9, 30),
                'end_time': datetime.time(17, 30),
                'date_time': 'Concluded September 2026',
                'mode': 'Hybrid (Campus & Online)',
                'venue': 'XEYR Engineering Center',
                'organizer': 'XEYR Core Engineering Team',
                'eligibility': 'Selected Cohort of 45 Engineering Students',
                'max_participants': 45,
                'is_paid': False,
                'fee': 'Free',
                'fee_amount': 0.00,
                'currency': 'INR',
                'is_published': True,
                'description': 'A 4-week intensive commercial engineering bootcamp training students on production Django, React, and PostgreSQL architectures.',
                'full_description': 'Students built real-world enterprise applications, worked with Git workflows, implemented automated test suites, and deployed cloud services with zero-downtime CI/CD pipelines.',
                'contact_email': 'alumni@xeyr.in',
                'contact_phone': '+91 80562 53897'
            }
        )

        # 3. Seed Social Media Configurations
        social_defaults = [
            ('instagram', 'Instagram', 'https://instagram.com/xeyrtechnologies', True),
            ('linkedin', 'LinkedIn', 'https://linkedin.com/company/xeyrtechnologies', True),
            ('github', 'GitHub', 'https://github.com/xeyrtechnologies', True),
            ('youtube', 'YouTube', 'https://youtube.com/@xeyrtechnologies', True),
        ]
        for key, name, url, pub in social_defaults:
            SocialMediaConfig.objects.get_or_create(
                platform_key=key,
                defaults={
                    'platform_name': name,
                    'platform_url': url,
                    'is_public': pub
                }
            )

        # Seed sample subscriber
        EventNotificationSubscriber.objects.get_or_create(
            email='subscriber.preview@xeyr.in',
            defaults={
                'full_name': 'Santhosh Tech Enthusiast',
                'consent_given': True,
                'categories_of_interest': 'Workshop, Masterclass'
            }
        )

        # 3. Seed Realistic Foundational Enquiries & Qualification Workflow
        # Project A: Qualified and ready for handover
        enq_a, _ = Enquiry.objects.get_or_create(
            reference_id='XEYR-ENQ-2026-1001',
            defaults={
                'client_name': 'Apex Logistics Private Limited',
                'contact_person': 'Ramesh Narayanan',
                'email': 'ramesh@apexlogistics.com',
                'phone': '+91 98400 11223',
                'organisation_type': 'Corporate / Logistics',
                'service_type': 'SolveX - Software / Digital',
                'project_title': 'Smart Warehouse & Fleet Dispatch Platform',
                'project_description': 'End-to-end web portal and mobile app for tracking driver dispatches and automated inventory billing.',
                'budget_range': '₹5,00,000 - ₹10,00,000',
                'expected_timeline': '3 Months',
                'source': 'Website (solvex-enquiry)',
                'status': EnquiryStatus.QUALIFIED,
                'assigned_to': sales_user
            }
        )

        EnquiryQualification.objects.get_or_create(
            enquiry=enq_a,
            defaults={
                'decision': 'High-Value Enterprise Digital Solution',
                'business_opportunity': 'Fleet management solution replacing manual paper logs with automated dispatch.',
                'client_needs': 'Real-time vehicle tracking, driver mobile app, invoicing portal.',
                'service_fit': 'SolveX Custom Engineering & Cloud Backend',
                'estimated_project_value': 750000.00,
                'budget_confirmed': True,
                'timeline_confirmed': True,
                'decision_maker_details': 'Managing Director & CTO',
                'technical_feasibility': 'High - standard Django backend with PostgreSQL and React frontend',
                'internal_assessment': 'Approved for requirements sign-off and immediate handover generation.',
                'account_manager': sales_user,
                'next_action': 'Developer Handover ZIP Generation',
                'qualified_by': admin_user
            }
        )

        # Requirements Workspace for Project A
        req_a, _ = ProjectRequirement.objects.get_or_create(
            enquiry=enq_a,
            defaults={
                'requirement_reference': 'XEYR-REQ-2026-1001',
                'project_name': 'Apex Smart Dispatch & Fleet OS',
                'status': RequirementStatus.APPROVED,
                'legal_business_name': 'Apex Logistics Private Limited',
                'client_contact_person': 'Ramesh Narayanan',
                'official_email': 'ramesh@apexlogistics.com',
                'official_phone': '+91 98400 11223',
                'business_address': 'Plot 45, Guindy Industrial Estate, Chennai - 600032',
                'industry_category': 'Supply Chain & Logistics',
                'website_and_socials': 'https://apexlogistics.example.com',
                'business_problem': 'Dispatch errors and delayed invoice turnaround causing cashflow bottlenecks.',
                'project_goals': 'Automate driver dispatch routing, reduce transit delays, generate live delivery receipts.',
                'target_audience': 'Warehouse staff, fleet managers, truck drivers, commercial accounts.',
                'expected_deliverables': ['Admin Dispatch Web Portal', 'Driver Mobile Progressive Web App', 'PostgreSQL Database Schema', 'REST API Suite'],
                'scope_of_work': 'Complete frontend, backend, database migrations, authentication, real-time map tracking, invoice exports.',
                'features_required': ['Driver trip logs', 'Vehicle GPS tracking', 'Automated tax invoices', 'Role permissions'],
                'functional_requirements': 'Dispatcher creates trip -> Driver accepts trip -> Status updates live -> Delivery OTP confirmed -> Automated invoice generated.',
                'non_functional_requirements': 'Sub-second API response time, 99.9% uptime, HTTPS encryption, zero data loss.',
                'technical_preferences': 'Django REST Framework, PostgreSQL 17, Celery, Chart.js',
                'integrations_required': 'SMS Gateway for OTPs, Email invoicing',
                'accessibility_responsive_reqs': 'Desktop widescreen console for dispatchers; lightweight mobile UI for drivers.',
                'hosting_deployment_reqs': 'Ubuntu 24.04 LTS VPS, Docker, NGINX reverse proxy, SSL certificate.',
                'quoted_price': 800000.00,
                'approved_budget': 750000.00,
                'payment_milestones': [
                    {'title': 'Sprint 1: Architecture & APIs', 'amount': 250000.00},
                    {'title': 'Sprint 2: Dispatch & Driver App', 'amount': 300000.00},
                    {'title': 'Sprint 3: QA & Production Deployment', 'amount': 200000.00}
                ],
                'commercial_approval_status': 'Approved',
                'design_style': 'Modern Dark Navy & High-Contrast Blue Accent',
                'color_preferences': '#07132e (Primary Navy), #1465f4 (Electric Blue), #10b981 (Success Green)',
                'typography_preferences': 'DM Sans / Manrope',
                'preferred_framework': 'Python Django 5.2 + Django REST Framework',
                'database_requirements': 'PostgreSQL 17 with spatial indexes',
                'security_requirements': 'CSRF protection, JWT session tokens, encrypted file uploads',
                'deployment_platform': 'Linux VPS (Docker Compose)',
                'testing_requirements': 'Automated unit tests for booking logic and invoicing calculations.',
                'acceptance_criteria': 'All 4 deliverables operational, tests passing, zero unhandled 500 errors.',
                'priority': 'High',
                'expected_start_date': timezone.now().date(),
                'expected_delivery_date': (timezone.now() + timezone.timedelta(days=90)).date(),
                'developer_assigned': dev_user,
                'project_manager_assigned': pm_user,
                'created_by': admin_user
            }
        )

        # Brand Asset for Project A
        asset_a, _ = ClientBrandAsset.objects.get_or_create(
            requirement=req_a,
            category=AssetCategory.PRIMARY_LOGO,
            defaults={
                'title': 'Apex Logistics Primary Vector Logo',
                'filename': 'apex_logistics_logo.svg',
                'file_type': 'image/svg+xml',
                'status': AssetStatus.APPROVED,
                'version': 1,
                'is_latest': True,
                'notes': 'Official vector logo approved by client marketing team.',
                'uploaded_by': admin_user
            }
        )

        # Generate Handover ZIP for Project A
        generator = HandoverZipGenerator(req_a, admin_user, exception_notes="Approved for developer assignment")
        handover_record = generator.generate(force_with_exception=True)
        handover_record.assigned_developer = dev_user
        handover_record.save()

        # Developer Project for Project A
        prj_a, _ = DeveloperProject.objects.get_or_create(
            requirement=req_a,
            defaults={
                'handover': handover_record,
                'project_code': 'XEYR-PRJ-2026-1001',
                'title': 'Apex Smart Dispatch & Fleet OS',
                'assigned_developer': dev_user,
                'project_manager': pm_user,
                'status': ProjectStatus.IN_PROGRESS,
                'priority': 'High',
                'progress_percentage': 35,
                'start_date': timezone.now().date(),
                'expected_completion_date': (timezone.now() + timezone.timedelta(days=75)).date(),
                'developer_notes': 'Database schema completed. Building REST endpoints for trip dispatching.'
            }
        )

        ProjectMilestone.objects.get_or_create(
            project=prj_a,
            title='Milestone 1: Database Architecture & Core API Endpoints',
            defaults={
                'due_date': timezone.now().date() + timezone.timedelta(days=15),
                'completed': True,
                'completed_at': timezone.now()
            }
        )
        ProjectMilestone.objects.get_or_create(
            project=prj_a,
            title='Milestone 2: Dispatcher Dashboard & Driver Web App',
            defaults={
                'due_date': timezone.now().date() + timezone.timedelta(days=45),
                'completed': False
            }
        )

        # Financial Record for Project A
        inv_a, _ = InvoiceQuote.objects.get_or_create(
            reference_no='XEYR-INV-2026-1001',
            defaults={
                'requirement': req_a,
                'project': prj_a,
                'doc_type': InvoiceQuote.DocType.INVOICE,
                'amount_quoted': 800000.00,
                'amount_approved': 750000.00,
                'amount_invoiced': 250000.00,
                'amount_received': 250000.00,
                'amount_pending': 0.00,
                'status': InvoiceQuote.Status.PAID,
                'created_by': admin_user
            }
        )
        PaymentRecord.objects.get_or_create(
            transaction_reference='TXN-HDFC-99882211',
            defaults={
                'invoice': inv_a,
                'project': prj_a,
                'payment_method': PaymentRecord.PaymentMethod.BANK_TRANSFER,
                'amount': 250000.00,
                'payment_status': PaymentRecord.PaymentStatus.VERIFIED,
                'notes': 'Advance milestone payment for Sprint 1.',
                'verified_by': admin_user
            }
        )

        # Project B: Documented Rejection with Mandatory Reason
        enq_b, _ = Enquiry.objects.get_or_create(
            reference_id='XEYR-ENQ-2026-1002',
            defaults={
                'client_name': 'QuickBites Food Delivery',
                'contact_person': 'Anand Verma',
                'email': 'anand@quickbites.in',
                'phone': '+91 99620 44556',
                'organisation_type': 'Startup',
                'service_type': 'SolveX - Software / Digital',
                'project_title': 'Instant Grocery Delivery App',
                'project_description': 'Need full clone of Zepto within 5 days for ₹15,000.',
                'budget_range': 'Under ₹50,000',
                'expected_timeline': '5 Days',
                'source': 'Website (solvex-enquiry)',
                'status': EnquiryStatus.REJECTED
            }
        )
        EnquiryRejection.objects.get_or_create(
            enquiry=enq_b,
            category=RejectionCategory.BUDGET_MISMATCH,
            defaults={
                'reason_detail': 'Client budget of ₹15,000 and 5-day delivery deadline are infeasible for full multi-tier delivery infrastructure.',
                'internal_notes': 'Proposed standard SolveX starter package, but client budget was strictly fixed.',
                'previous_status': EnquiryStatus.NEW,
                'future_followup_appropriate': False,
                'rejected_by': admin_user
            }
        )

        # Project C: SkillBridge College Request
        enq_c, _ = Enquiry.objects.get_or_create(
            reference_id='XEYR-ENQ-2026-1003',
            defaults={
                'client_name': 'KCG Institute of Engineering & Technology',
                'contact_person': 'Dr. K. Swaminathan (HOD CSE)',
                'email': 'hod.cse@kcginstitute.edu.in',
                'phone': '+91 94440 55667',
                'organisation_type': 'College / University',
                'service_type': 'SkillBridge - College Workshop',
                'project_title': 'Two-Day Hands-on Workshop on GenAI & LLM Workflows',
                'project_description': 'Hands-on practical training for 120 final-year computer science students.',
                'budget_range': '₹50,000 - ₹2,00,000',
                'expected_timeline': 'Next Month',
                'source': 'Website (college-service-enquiry)',
                'status': EnquiryStatus.UNDER_REVIEW,
                'assigned_to': sales_user
            }
        )

        # Operational Expenses
        ExpenseRecord.objects.get_or_create(
            title='AWS Cloud Hosting & PostgreSQL Cluster',
            date=timezone.now().date(),
            defaults={
                'category': ExpenseRecord.ExpenseCategory.SOFTWARE_HOSTING,
                'amount': 18500.00,
                'notes': 'Production compute and database cluster hosting.',
                'recorded_by': admin_user
            }
        )

        self.stdout.write(self.style.SUCCESS("XEYR Database successfully seeded with real verified business data."))
