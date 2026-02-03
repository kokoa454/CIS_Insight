from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from datetime import timedelta

from .models import PreUser

# 仮登録ユーザーの削除
def delete_pre_user():
    for pre_user in PreUser.objects.filter(is_verified = True):
        print(pre_user.pre_user_email + " is verified")
        pre_user.delete()
    for pre_user in PreUser.objects.filter(pre_user_created_at__lt = timezone.now() - timedelta(minutes = 30)):
        print(pre_user.pre_user_email + " is deleted")
        pre_user.delete()

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(delete_pre_user, 'interval', minutes = 1)
    scheduler.start()
