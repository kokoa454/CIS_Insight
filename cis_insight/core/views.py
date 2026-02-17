from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django_ratelimit.decorators import ratelimit
import json
import secrets
import logging
import threading

from .settings import (LOGO_PATH, SITE_URL, EMAIL_HOST_USER, COUNTRIES, CIS_COUNTRIES, MAXIMUM_EMAIL_LENGTH, PRE_USER_EXPIRATION_TIME_MINUTES, VALIDATION_CODE_LENGTH)
from users.models import (PreUser, PreUserManager, User)

logger = logging.getLogger(__name__)

# ランディングページ関連
def render_landing_page(request):
    return render(request, 'landing.html', {
        'logo_path': LOGO_PATH,
        'countries': COUNTRIES,
        'cis_countries': CIS_COUNTRIES
    })

# ユーザー登録前の仮登録関連
@ratelimit(key = 'ip', rate = '5/m', block = True)
def pre_sign_up(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')

        if not email:
            return JsonResponse({'status': 'error', 'message': 'メールアドレスを入力してください。'})

        try:
            validate_email(email)
        except ValidationError:
            logger.error(f'Invalid email format: {email}')
            return JsonResponse({'status': 'error', 'message': 'メールアドレスの形式が正しくありません。'})

        if len(email) > MAXIMUM_EMAIL_LENGTH:
            return JsonResponse({'status': "error", "message" : "メールアドレスは" + str(MAXIMUM_EMAIL_LENGTH) + "文字以内で入力してください。"})

        if PreUser.objects.filter(email = email).exists():
            logger.error(f'Email already exists in pre_user: {email}')
            return JsonResponse({'status': 'error', 'message': 'このメールアドレスはすでに仮登録されています。メールボックスを確認してください。もしメールが届かない場合は、30分後に再度お試しください。'})

        if User.objects.filter(email = email).exists():
            logger.error(f'Email already exists in user: {email}')
            return JsonResponse({'status': 'error', 'message': 'このメールアドレスはすでに本登録されています。'})

        verification_code = generate_verification_code()
        PreUser.objects.create_pre_user(email, verification_code)

        if not send_verification_email(email, verification_code):
            return JsonResponse({'status': 'error', 'message': '申し訳ありません。メールの送信に失敗しました。時間を空けてから再度お試しください。'})

        logger.info(f'User {email} pre-registered successfully')
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f'Exception in pre_sign_up with email: {email}: {e}')
        return JsonResponse({'status': 'error', 'message': '申し訳ありません。仮登録に失敗しました。時間を空けてから再度お試しください。', 'error_message': str(e)})

def generate_verification_code():
    return secrets.token_hex(VALIDATION_CODE_LENGTH)

def send_verification_email(email, verification_code):
    try:
        subject = "CIS Insight - アカウント登録用リンク"
        message = f"CIS Insightへようこそ。下記の内容で仮登録を受け付けました。\n\nメールアドレス: {email}\n\n以下のリンクで本登録を完了してください。\n有効期限は{PRE_USER_EXPIRATION_TIME_MINUTES}分です。なお、このメールは自動送信のため、返信はできません。\n\n{SITE_URL}/sign_up/{verification_code}"
        send_mail(subject, message, EMAIL_HOST_USER, [email], fail_silently=False)
        logger.info(f'Email sent to: {email}')
        return True
    except Exception as e:
        logger.error(f'Exception in send_verification_email: {e}')
        return False

# エラーページ関連
def render_error_page(request):
    return render(request, 'error.html')