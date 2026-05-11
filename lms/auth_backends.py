import json
import logging
from urllib import error, request

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend


logger = logging.getLogger(__name__)


class NPUStudentAPIBackend(BaseBackend):
    """Authenticate NPU students against the university student LDAP API."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not getattr(settings, 'NPU_STUDENT_AUTH_ENABLED', False):
            return None
        if not username or not password:
            return None
        if not self._looks_like_student_code(username):
            return None

        payload = self._authenticate_student(username, password)
        if not payload:
            return None

        student = payload.get('student_info') or {}
        student_code = student.get('student_code') or username
        if str(student_code) != str(username):
            logger.warning('NPU student API returned mismatched student_code for %s', username)
            return None

        User = get_user_model()
        user, _ = User.objects.get_or_create(username=student_code)
        self._update_user_from_student_info(user, student, payload.get('additional_info') or {})
        return user if self.user_can_authenticate(user) else None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None

    def user_can_authenticate(self, user):
        return getattr(user, 'is_active', True)

    def _authenticate_student(self, username, password):
        token = getattr(settings, 'NPU_STUDENT_AUTH_TOKEN', '')
        if not token:
            logger.debug('NPU student auth token is not configured')
            return None

        body = json.dumps({
            'userLdap': username,
            'passLdap': password,
        }).encode('utf-8')
        api_request = request.Request(
            getattr(settings, 'NPU_STUDENT_AUTH_URL'),
            data=body,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            method='POST',
        )

        try:
            with request.urlopen(api_request, timeout=getattr(settings, 'NPU_STUDENT_AUTH_TIMEOUT', 10)) as response:
                data = json.loads(response.read().decode('utf-8'))
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning('NPU student auth API failed for %s: %s', username, exc)
            return None

        if data.get('success') is True:
            return data
        return None

    def _looks_like_student_code(self, username):
        student_code_length = getattr(settings, 'NPU_STUDENT_CODE_LENGTH', 12)
        return username.isdigit() and len(username) == student_code_length

    def _update_user_from_student_info(self, user, student, additional):
        user.first_name = student.get('student_name') or ''
        user.last_name = student.get('student_surname') or ''
        user.email = student.get('email') or user.email

        faculty = student.get('faculty_name') or additional.get('faculty') or ''
        program = student.get('program_name') or additional.get('program') or ''
        user.department = ' / '.join(part for part in (faculty, program) if part)

        user.is_active = True
        user.is_staff = False
        user.set_unusable_password()
        user.save()
