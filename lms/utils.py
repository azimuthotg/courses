import os
from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string

from .models import Certificate


def mark_completed(user, course, progress):
    """Mark course as completed and auto-issue certificate (idempotent)."""
    if progress.status != 'completed':
        progress.status = 'completed'
        progress.save()
    Certificate.objects.get_or_create(user=user, course=course)


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
