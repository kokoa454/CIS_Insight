from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from datetime import timedelta

from .models import PreUser
from .models import PasswordChange

# 仮登録ユーザーの削除
def delete_pre_user():
    for pre_user in PreUser.objects.filter(is_verified = True):
        print(pre_user.pre_user_email + " is verified")
        pre_user.delete()
    for pre_user in PreUser.objects.filter(pre_user_created_at__lt = timezone.now() - timedelta(minutes = 30)):
        print(pre_user.pre_user_email + " is deleted")
        pre_user.delete()

# パスワード変更ユーザーの削除
def delete_password_change():
    for password_change in PasswordChange.objects.filter(is_verified = True):
        print(password_change.user.user_email + " is verified")
        password_change.delete()
    for password_change in PasswordChange.objects.filter(password_change_created_at__lt = timezone.now() - timedelta(minutes = 30)):
        print(password_change.user.user_email + " is deleted")
        password_change.delete()

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(delete_pre_user, 'interval', minutes = 1)
    scheduler.add_job(delete_password_change, 'interval', minutes = 1)
    scheduler.start()
