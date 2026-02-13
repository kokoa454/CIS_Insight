from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail

from .models import PreUser
from .models import User
from core.settings import (SITE_URL, EMAIL_HOST_USER)

# ユーザー登録ページ関連
def render_sign_up_page(request, verification_code):
    try:
        pre_user = PreUser.objects.get_pre_user(verification_code)
    except Exception as e:
        return render(request, 'error.html')
    
    if pre_user:
        user_email = pre_user.pre_user_email
        return render(request, 'sign_up.html', {'user_email': user_email, 'verification_code': verification_code})
    return render(request, 'error.html')

# ユーザー登録関連
@csrf_exempt
def sign_up(request):
    try:
        user_email = request.POST.get('email')
        user_name = request.POST.get('username')
        user_display_name = request.POST.get('display_name')
        password = request.POST.get('password')
        verification_code = request.POST.get('verification_code')

        if User.objects.is_user_email_duplicate(user_email):
            return JsonResponse({'status': "error", "message" : "すでに登録済みのメールアドレスです。"})
        
        if User.objects.is_user_name_duplicate(user_name):
            return JsonResponse({'status': "error", "message" : "ユーザー名が重複しています。"})
        
        User.objects.create_user(user_name, user_email, user_display_name, password)
        PreUser.objects.verify_pre_user(verification_code)
        
        send_sign_up_email(user_email, user_name, user_display_name)
        return JsonResponse({'status': "success"})
    except Exception as e:
        return JsonResponse({'status': "error", "message" : "登録に失敗しました。", "error_message": str(e)})

def send_sign_up_email(email, user_name, user_display_name):
    subject = "CIS Insight - アカウント登録完了"
    message = f"CIS Insightへの本登録が完了しました。\nアカウント登録内容は以下のとおりです。\n\nユーザー名: {user_name}\n表示名: {user_display_name}\nメールアドレス: {email}\n\n{SITE_URL}"
    send_mail(subject, message, EMAIL_HOST_USER, [email], fail_silently=False)
    return True