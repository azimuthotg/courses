import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)

LINE_PUSH_URL = 'https://api.line.me/v2/bot/message/push'


def send_line_push(line_user_id: str, message: str) -> bool:
    """Send a LINE Messaging API push message without interrupting user flow."""
    if not getattr(settings, 'LINE_OA_ENABLED', False):
        return False
    if not line_user_id:
        return False

    token = getattr(settings, 'LINE_OA_CHANNEL_ACCESS_TOKEN', '')
    if not token:
        logger.warning('LINE_OA_CHANNEL_ACCESS_TOKEN is not configured')
        return False

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'to': line_user_id,
        'messages': [{'type': 'text', 'text': message}],
    }

    try:
        response = requests.post(LINE_PUSH_URL, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return True
        logger.error('LINE push failed: %s %s', response.status_code, response.text)
        return False
    except requests.RequestException as exc:
        logger.error('LINE push error: %s', exc)
        return False


def notify_course_completed(user, course, certificate):
    """Notify a learner when a course is completed and a certificate is issued."""
    if not user.line_user_id:
        return False

    message = (
        f'ยินดีด้วยคุณ {user.get_full_name() or user.username}!\n'
        f'คุณเรียนจบวิชา "{course.title}" เรียบร้อยแล้ว\n'
        f'ใบประกาศนียบัตรของคุณพร้อมให้ดาวน์โหลดแล้ว\n'
        f'เลขที่: {certificate.serial_number}'
    )
    return send_line_push(user.line_user_id, message)
