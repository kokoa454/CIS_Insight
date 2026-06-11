import logging
from datetime import timedelta

from core.settings import (EMAIL_CHANGE_DELETION_TIME_MINUTES,
                           EMAIL_CHANGE_EXPIRATION_TIME_MINUTES,
                           PASSWORD_RESET_DELETION_TIME_MINUTES,
                           PASSWORD_RESET_EXPIRATION_TIME_MINUTES,
                           PRE_USER_DELETION_TIME_MINUTES,
                           PRE_USER_EXPIRATION_TIME_MINUTES)
from django.utils import timezone

from .models import EmailChange, PasswordReset, PreUser

logger = logging.getLogger(__name__)

# 仮登録ユーザーの有効期限切れ設定
def expire_pre_user():
    expired_pre_users = PreUser.objects.filter(
        created_at__lt = timezone.now() - timedelta(minutes = PRE_USER_EXPIRATION_TIME_MINUTES),
        is_expired = False
    )
    
    for pre_user in expired_pre_users:
        try:
            logger.info(f'PreUser expired: {pre_user.email}')
            pre_user.is_expired = True
            pre_user.save()
        except Exception as e:
            logger.error(f'Error expiring pre_user {pre_user.email}: {e}')

# 仮登録ユーザーの削除
def delete_pre_user():
    expired_pre_users = PreUser.objects.filter(
        created_at__lt = timezone.now() - timedelta(minutes = PRE_USER_DELETION_TIME_MINUTES)
    )
    
    try:
        expired_pre_users.delete()
        logger.info(f'Deleted {expired_pre_users.count()} pre_users')
    except Exception as e:
        logger.error(f'Error deleting pre_users: {e}')

# メール変更ユーザの有効期限切れ設定
def expire_email_change():
    expired_email_changes = EmailChange.objects.filter(
        created_at__lt = timezone.now() - timedelta(minutes = EMAIL_CHANGE_EXPIRATION_TIME_MINUTES),
        is_expired = False
    )

    for email_change in expired_email_changes:
        try:
            logger.info(f'EmailChange expired: {email_change.new_email}')
            email_change.is_expired = True
            email_change.save()
        except Exception as e:
            logger.error(f'Error expiring email_change {email_change.new_email}: {e}')

# メール変更ユーザの削除
def delete_email_change():
    expired_email_changes = EmailChange.objects.filter(
        created_at__lt = timezone.now() - timedelta(minutes = EMAIL_CHANGE_DELETION_TIME_MINUTES)
    )
    
    try:
        expired_email_changes.delete()
        logger.info(f'Deleted {expired_email_changes.count()} email_changes')
    except Exception as e:
        logger.error(f'Error deleting email_changes: {e}')

# パスワードリセットユーザの有効期限切れ設定
def expire_password_reset():
    expired_password_resets = PasswordReset.objects.filter(
        created_at__lt = timezone.now() - timedelta(minutes = PASSWORD_RESET_EXPIRATION_TIME_MINUTES),
        is_expired = False
    )

    for password_reset in expired_password_resets:
        try:
            logger.info(f'PasswordReset expired: {password_reset.user.username}')
            password_reset.is_expired = True
            password_reset.save()
        except Exception as e:
            logger.error(f'Error expiring password_reset {password_reset.user.username}: {e}')

# パスワードリセットユーザの削除
def delete_password_reset():
    expired_password_resets = PasswordReset.objects.filter(
        created_at__lt = timezone.now() - timedelta(minutes = PASSWORD_RESET_DELETION_TIME_MINUTES)
    )
    
    try:
        expired_password_resets.delete()
        logger.info(f'Deleted {expired_password_resets.count()} password_resets')
    except Exception as e:
        logger.error(f'Error deleting password_resets: {e}')
