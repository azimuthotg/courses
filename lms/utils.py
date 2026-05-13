import os
from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string

from .line_notify import notify_course_completed
from .models import AuditLog, Certificate


def mark_completed(user, course, progress):
    """Mark course as completed and auto-issue certificate (idempotent)."""
    was_completed = progress.status == 'completed'
    if progress.status != 'completed':
        progress.status = 'completed'
        progress.save()
    certificate, created = Certificate.objects.get_or_create(user=user, course=course)
    if not was_completed:
        log_audit(user, 'course_complete', course.title)
    if created:
        log_audit(user, 'certificate_issued', f'{course.title} | {certificate.serial_number}')
        notify_course_completed(user, course, certificate)


def log_audit(user, action, description='', request=None):
    """Write an audit log entry without interrupting the user flow."""
    try:
        ip_address = None
        if request:
            x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
            ip_address = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR')
        AuditLog.objects.create(
            user=user if getattr(user, 'is_authenticated', False) else None,
            action=action,
            description=description,
            ip_address=ip_address,
        )
    except Exception:
        pass


def link_callback(uri, rel):
    """Map static/media URLs to absolute filesystem paths for xhtml2pdf."""
    if uri.startswith(settings.STATIC_URL):
        static_path = uri.replace(settings.STATIC_URL, '').lstrip('/')
        path = finders.find(static_path)
        if not path:
            path = os.path.join(settings.STATIC_ROOT, static_path)
    elif uri.startswith(settings.MEDIA_URL):
        path = os.path.join(
            settings.MEDIA_ROOT,
            uri.replace(settings.MEDIA_URL, '').lstrip('/')
        )
    else:
        return uri
    return path


def generate_certificate_pdf(user, course, certificate):
    """Render certificate HTML and convert to PDF buffer using xhtml2pdf."""
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return None

    html_string = render_to_string('lms/certificate_template.html', {
        'user': user,
        'course': course,
        'certificate': certificate,
    })
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=buffer, link_callback=link_callback)
    if pisa_status.err:
        return None
    buffer.seek(0)
    return buffer
