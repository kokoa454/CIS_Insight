from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from datetime import timedelta
import logging

from .models import PreUser, EmailChange
from core.settings import (PRE_USER_EXPIRATION_TIME_MINUTES, PRE_USER_DELETION_TIME_MINUTES, EMAIL_CHANGE_EXPIRATION_TIME_MINUTES, EMAIL_CHANGE_DELETION_TIME_MINUTES)

logger = logging.getLogger(__name__)

# 仮登録ユーザーの有効期限切れ設定
def expire_pre_user():
    expired_pre_users = PreUser.objects.filter(created_at__lt = timezone.now() - timedelta(minutes = PRE_USER_EXPIRATION_TIME_MINUTES)) and PreUser.objects.filter(is_expired = False)
    
    for pre_user in expired_pre_users:
        logger.info(f'PreUser expired: {pre_user.email}')
        pre_user.is_expired = True
        pre_user.save()

# 仮登録ユーザーの削除
def delete_pre_user():
    expired_pre_users = PreUser.objects.filter(created_at__lt = timezone.now() - timedelta(minutes = PRE_USER_DELETION_TIME_MINUTES))
    
    for pre_user in expired_pre_users:
        logger.info(f'PreUser deleted: {pre_user.email}')

    expired_pre_users.delete()

# メール変更ユーザの有効期限切れ設定
def expire_email_change():
    expired_email_changes = EmailChange.objects.filter(created_at__lt = timezone.now() - timedelta(minutes = EMAIL_CHANGE_EXPIRATION_TIME_MINUTES)) and EmailChange.objects.filter(is_expired = False)
    
    for email_change in expired_email_changes:
        logger.info(f'EmailChange expired: {email_change.new_email}')
        email_change.is_expired = True
        email_change.save()

# メール変更ユーザの削除
def delete_email_change():
    expired_email_changes = EmailChange.objects.filter(created_at__lt = timezone.now() - timedelta(minutes = EMAIL_CHANGE_DELETION_TIME_MINUTES))
    
    for email_change in expired_email_changes:
        logger.info(f'EmailChange deleted: {email_change.new_email}')

    expired_email_changes.delete()

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(expire_pre_user, 'interval', minutes = 1)
    scheduler.add_job(delete_pre_user, 'interval', minutes = 1)
    scheduler.add_job(expire_email_change, 'interval', minutes = 1)
    scheduler.add_job(delete_email_change, 'interval', minutes = 1)
    scheduler.start()
