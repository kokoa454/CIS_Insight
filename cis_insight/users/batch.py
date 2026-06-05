import logging
from datetime import timedelta

from core.settings import (EMAIL_CHANGE_DELETION_TIME_MINUTES,
                           EMAIL_CHANGE_EXPIRATION_TIME_MINUTES,
                           PRE_USER_DELETION_TIME_MINUTES,
                           PRE_USER_EXPIRATION_TIME_MINUTES)
from django.utils import timezone

from .models import EmailChange, PreUser

logger = logging.getLogger(__name__)

# 仮登録ユーザーの有効期限切れ設定
def expire_pre_user():
    expired_pre_users = PreUser.objects.filter(
        created_at__lt = timezone.now() - timedelta(minutes = PRE_USER_EXPIRATION_TIME_MINUTES),
        is_expired = False
    )
    
    for pre_user in expired_pre_users:
        logger.info(f'PreUser expired: {pre_user.email}')
        pre_user.is_expired = True
        pre_user.save()

# 仮登録ユーザーの削除
def delete_pre_user():
    expired_pre_users = PreUser.objects.filter(
        created_at__lt = timezone.now() - timedelta(minutes = PRE_USER_DELETION_TIME_MINUTES)
    )
    
    for pre_user in expired_pre_users:
        logger.info(f'PreUser deleted: {pre_user.email}')

    expired_pre_users.delete()

# メール変更ユーザの有効期限切れ設定
def expire_email_change():
    expired_email_changes = EmailChange.objects.filter(
        created_at__lt = timezone.now() - timedelta(minutes = EMAIL_CHANGE_EXPIRATION_TIME_MINUTES),
        is_expired = False
    )
    
    for email_change in expired_email_changes:
        logger.info(f'EmailChange expired: {email_change.new_email}')
        email_change.is_expired = True
        email_change.save()

# メール変更ユーザの削除
def delete_email_change():
    expired_email_changes = EmailChange.objects.filter(
        created_at__lt = timezone.now() - timedelta(minutes = EMAIL_CHANGE_DELETION_TIME_MINUTES)
    )
    
    for email_change in expired_email_changes:
        logger.info(f'EmailChange deleted: {email_change.new_email}')

    expired_email_changes.delete()
