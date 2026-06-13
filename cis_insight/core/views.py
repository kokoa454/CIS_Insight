import json
import logging

from core.utils import generate_verification_code
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from news.models import CisAndNeighborCountry, CisCountry
from users.models import PasswordReset, PreUser, User

from .settings import (EMAIL_HOST_USER, LOGO_PATH, MAXIMUM_EMAIL_LENGTH,
                       PASSWORD_RESET_EXPIRATION_TIME_MINUTES,
                       PRE_USER_EXPIRATION_TIME_MINUTES, SITE_URL)

logger = logging.getLogger(__name__)

# ランディングページ関連
def render_landing_page(request):
    countries = CisAndNeighborCountry.objects.all()
    cis_countries = CisCountry.objects.all()
    return render(request, 'landing.html', {
        'logo_path': LOGO_PATH,
        'countries': countries,
        'cis_countries': cis_countries
    })

def pre_sign_up_error(request):
    return JsonResponse({'status': 'error', 'message': '新規ユーザ登録は現在受け付けておりません。'})

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
            logger.warning(f'Invalid email format: {email}')
            return JsonResponse({'status': 'error', 'message': 'メールアドレスの形式が正しくありません。'})

        if len(email) > MAXIMUM_EMAIL_LENGTH:
            return JsonResponse({'status': "error", "message" : "メールアドレスは" + str(MAXIMUM_EMAIL_LENGTH) + "文字以内で入力してください。"})

        if PreUser.objects.filter(email = email).exists():
            logger.warning(f'Email already exists in pre_user: {email}')
            return JsonResponse({'status': 'error', 'message': 'このメールアドレスはすでに仮登録されています。メールボックスを確認してください。もしメールが届かない場合は、30分後に再度お試しください。'})

        if User.objects.filter(email = email).exists():
            logger.warning(f'Email already exists in user: {email}')
            return JsonResponse({'status': 'error', 'message': 'このメールアドレスはすでに本登録されています。'})

        verification_code = generate_verification_code()

        pre_user, created = PreUser.objects.get_or_create(
            email = email,
            defaults = {
                'verification_code': verification_code
            }
        )

        if created:
            if not send_verification_email(email, verification_code):
                return JsonResponse({'status': 'error', 'message': '申し訳ありません。メールの送信に失敗しました。時間を空けてから再度お試しください。'})
        else:
            return JsonResponse({'status': 'error', 'message': 'このメールアドレスはすでに仮登録されています。メールボックスを確認してください。もしメールが届かない場合は、30分後に再度お試しください。'})

        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f'Exception in pre_sign_up: {e}')
        return JsonResponse({'status': 'error', 'message': '申し訳ありません。仮登録に失敗しました。時間を空けてから再度お試しください。'})

def send_verification_email(email, verification_code):
    try:
        subject = "CIS Insight - アカウント登録用リンク"
        message = f"CIS Insightへようこそ。下記の内容で仮登録を受け付けました。\n\nメールアドレス: {email}\n\n以下のリンクで本登録を完了してください。\n有効期限は{PRE_USER_EXPIRATION_TIME_MINUTES}分です。なお、このメールは自動送信のため、返信はできません。\n\n{SITE_URL}/sign_up/{verification_code}"
        send_mail(subject, message, EMAIL_HOST_USER, [email], fail_silently=False)
        return True
    except Exception as e:
        logger.error(f'Exception in send_verification_email: {e}')
        return False

# パスワードリセット関連
def send_password_reset_email(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')

        if not email:
            return JsonResponse({'status': 'error', 'message': 'メールアドレスを入力してください。'})

        try:
            validate_email(email)
        except ValidationError:
            logger.warning(f'Invalid email format: {email}')
            return JsonResponse({'status': 'error', 'message': 'メールアドレスの形式が正しくありません。'})

        if User.objects.filter(email = email).exists():
            user = User.objects.get(email = email)
            verification_code = generate_verification_code()

            password_reset, created = PasswordReset.objects.get_or_create(
                user = user,
                defaults = {
                    'verification_code': verification_code
                }
            )

            if created:
                try:
                    subject = "CIS Insight - パスワードリセット用リンク"
                    message = f"CIS Insightをご利用いただきありがとうございます。パスワードリセット用のリンクを送信します。\n\nメールアドレス: {email}\n\n以下のリンクでパスワードリセットを行ってください。\n有効期限は{PASSWORD_RESET_EXPIRATION_TIME_MINUTES}分です。なお、このメールは自動送信のため、返信はできません。\n\n{SITE_URL}/password_reset/{verification_code}"
                    send_mail(subject, message, EMAIL_HOST_USER, [email], fail_silently=False)
                    return JsonResponse({'status': 'success'})
                except Exception as e:
                    logger.error(f'Exception in send_password_reset_email: {e}')
                    return JsonResponse({'status': 'error', 'message': 'パスワードリセット用のメールの送信に失敗しました。'})
            else:
                return JsonResponse({'status': 'error', 'message': 'すでにパスワードリセット用のメールが送信されています。'})
        else:
            return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f'Exception in send_password_reset_email: {e}')
        return JsonResponse({'status': 'error', 'message': 'パスワードリセット用のメールの送信に失敗しました。'})

# エラーページ関連
def render_error_page(request, error_code, error_message):
    return render(request, 'error.html', {'error_code': error_code, 'error_message': error_message})

def error_400(request, exception = None):
    return render_error_page(request, '400', 'Bad request')

def error_403(request, exception = None):
    return render_error_page(request, '403', 'Forbidden')

def error_404(request, exception = None):
    return render_error_page(request, '404', 'Page not found')

def error_500(request, exception = None):
    return render_error_page(request, '500', 'Internal server error')
