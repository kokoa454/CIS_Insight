from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .models import PreUser
from .models import PasswordChange

logger = logging.getLogger(__name__)

# 仮登録ユーザーの削除
@shared_task
def delete_pre_user():
    verified_pre_users = PreUser.objects.filter(is_verified = True)
    expired_pre_users = PreUser.objects.filter(pre_user_created_at__lt = timezone.now() - timedelta(minutes = 30))
    
    for pre_user in verified_pre_users:
        logger.info(f'PreUser verified: {pre_user}')
        
    for pre_user in expired_pre_users:
        logger.info(f'PreUser expired: {pre_user}')

    verified_pre_users.delete()
    expired_pre_users.delete()

# パスワード変更ユーザーの削除
@shared_task
def delete_password_change():
    verified_password_changes = PasswordChange.objects.filter(is_verified = True)
    expired_password_changes = PasswordChange.objects.filter(password_change_created_at__lt = timezone.now() - timedelta(minutes = 30))
    
    for password_change in verified_password_changes:
        logger.info(f'PasswordChange verified: {password_change}')
        
    for password_change in expired_password_changes:
        logger.info(f'PasswordChange expired: {password_change}')
        
    verified_password_changes.delete()
    expired_password_changes.delete()
