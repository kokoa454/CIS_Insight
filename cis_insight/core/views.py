from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import json
import secrets

from .settings import (LOGO_PATH, SITE_URL, EMAIL_HOST_USER, COUNTRIES, CIS_COUNTRIES)
from users.models import (PreUser, PreUserManager, User)

# ランディングページ関連
def render_landing_page(request):
    return render(request, 'landing.html', {
        'logo_path': LOGO_PATH,
        'countries': COUNTRIES,
        'cis_countries': CIS_COUNTRIES
    })

# ユーザー登録前の仮登録関連
@csrf_exempt
def pre_sign_up(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')

        if PreUser.objects.filter(pre_user_email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'このメールアドレスはすでに仮登録されています。メールボックスを確認してください。もしメールが届かない場合は、30分後に再度お試しください。'})

        if User.objects.filter(user_email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'このメールアドレスはすでに本登録されています。'})

        verification_code = generate_verification_code()
        PreUser.objects.create_pre_user(email, verification_code)
        send_verification_email(email, verification_code)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': '申し訳ありません。仮登録に失敗しました。時間を空けてから再度お試しください。', 'error_message': str(e)})

def generate_verification_code():
    return secrets.token_hex(32)

def send_verification_email(email, verification_code):
    subject = "CIS Insight - アカウント登録用リンク"
    message = f"CIS Insightへようこそ。下記の内容で仮登録を受け付けました。\n\nメールアドレス: {email}\n\n以下のリンクで本登録を完了してください。\n有効期限は30分です。なお、このメールは自動送信のため、返信はできません。\n\n{SITE_URL}/sign_up/{verification_code}"
    send_mail(subject, message, EMAIL_HOST_USER, [email], fail_silently=False)
    return True

# エラーページ関連
def render_error_page(request):
    return render(request, 'error.html')