import os
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


class PublicWebsiteView(APIView):
    """
    Serves the preserved existing public website.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        frontend_dir = settings.BASE_DIR.parent / 'XEYR_Website_Frontend'
        index_file = frontend_dir / 'index.html'
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return HttpResponse(content, content_type='text/html; charset=utf-8')
        return HttpResponse("<h1>XEYR Technologies Frontend</h1><p>Website files located in XEYR_Website_Frontend.</p>")


class AdminDashboardView(APIView):
    """
    Serves the XEYR Business OS Administration Dashboard.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        dashboard_file = settings.BASE_DIR / 'templates' / 'dashboard.html'
        if os.path.exists(dashboard_file):
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return HttpResponse(content, content_type='text/html; charset=utf-8')
        return HttpResponse("<h1>XEYR Admin Dashboard</h1><p>Dashboard template is being initialized.</p>")


class EventsPortalView(APIView):
    """
    Serves the dedicated public Events Portal.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        frontend_dir = settings.BASE_DIR.parent / 'XEYR_Website_Frontend'
        events_file = frontend_dir / 'events.html'
        if os.path.exists(events_file):
            with open(events_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return HttpResponse(content, content_type='text/html; charset=utf-8')
        return HttpResponse("<h1>XEYR Events Portal</h1><p>Events portal is loading...</p>")


class EventDetailPageView(APIView):
    """
    Serves the individual public event detail & registration split-screen page.
    """
    permission_classes = [AllowAny]

    def get(self, request, slug=None):
        frontend_dir = settings.BASE_DIR.parent / 'XEYR_Website_Frontend'
        event_file = frontend_dir / 'event.html'
        if os.path.exists(event_file):
            with open(event_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return HttpResponse(content, content_type='text/html; charset=utf-8')
        return HttpResponse("<h1>XEYR Event Details</h1><p>Event page is loading...</p>")


class ParticipantDashboardPageView(APIView):
    """
    Serves the Participant My Dashboard page.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        frontend_dir = settings.BASE_DIR.parent / 'XEYR_Website_Frontend'
        dash_file = frontend_dir / 'dashboard.html'
        if os.path.exists(dash_file):
            with open(dash_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return HttpResponse(content, content_type='text/html; charset=utf-8')
        return HttpResponse("<h1>XEYR Participant Dashboard</h1><p>Dashboard is loading...</p>")


class CertificateVerifyPageView(APIView):
    """
    Serves the public certificate verification page.
    """
    permission_classes = [AllowAny]

    def get(self, request, certificate_id=None):
        frontend_dir = settings.BASE_DIR.parent / 'XEYR_Website_Frontend'
        cert_file = frontend_dir / 'verify-certificate.html'
        if os.path.exists(cert_file):
            with open(cert_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return HttpResponse(content, content_type='text/html; charset=utf-8')
        return HttpResponse("<h1>XEYR Certificate Verification</h1><p>Verification system is loading...</p>")

