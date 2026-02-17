from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from datetime import timedelta
import logging

from .models import PreUser
from .models import PasswordChange
from core.settings import (PRE_USER_EXPIRATION_TIME_MINUTES, PRE_USER_DELETION_TIME_MINUTES)

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
        logger.info(f'PreUser expired: {pre_user.email}')

    expired_pre_users.delete()

# パスワード変更ユーザーの削除
def delete_password_change():
    verified_password_changes = PasswordChange.objects.filter(is_verified = True)
    expired_password_changes = PasswordChange.objects.filter(password_change_created_at__lt = timezone.now() - timedelta(minutes = 30))
    
    for password_change in verified_password_changes:
        logger.info(f'PasswordChange verified: {password_change}')
    
    verified_password_changes.delete()
    
    for password_change in expired_password_changes:
        logger.info(f'PasswordChange expired: {password_change}')
    
    expired_password_changes.delete()

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(expire_pre_user, 'interval', minutes = 1)
    scheduler.add_job(delete_pre_user, 'interval', minutes = 1)
    scheduler.add_job(delete_password_change, 'interval', minutes = 1)
    scheduler.start()
