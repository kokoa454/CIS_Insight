from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
import re
import random
import string

from .models import PreUser
from .models import User
from core.settings import (SITE_URL, EMAIL_HOST_USER, CIS_COUNTRIES, TOPICS)

# ユーザ登録ページ関連
def render_sign_up_page(request, verification_code):
    try:
        pre_user = PreUser.objects.get_pre_user(verification_code)
    except Exception as e:
        return render(request, 'error.html')
    
    if pre_user:
        user_email = pre_user.pre_user_email
        return render(request, 'sign_up.html', {'user_email': user_email, 'verification_code': verification_code})
    return render(request, 'error.html')

# ユーザ登録関連
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

        registered_user_email = PreUser.objects.get_pre_user(verification_code).pre_user_email
        if registered_user_email != user_email:
            return JsonResponse({'status': "error", "message" : "登録済みのメールアドレスと一致しません。"})

        if len(user_name) > 16 or not re.match(r'^[a-zA-Z0-9_]+$', user_name):
            return JsonResponse({'status': "error", "message" : "不正な入力です。"})
        
        if len(user_display_name) > 16:
            return JsonResponse({'status': "error", "message" : "不正な入力です。"})
        
        if len(password) < 8:
            return JsonResponse({'status': "error", "message" : "不正な入力です。"})

        user = User.objects.create_user(user_name, user_email, user_display_name, password)
        PreUser.objects.verify_pre_user(verification_code)

        login(request, user)
        
        send_sign_up_email(user_email, user_name, user_display_name)
        return JsonResponse({'status': "success"})
    except Exception as e:
        print(e)
        return JsonResponse({'status': "error", "message" : "登録に失敗しました。", "error_message": str(e)})

def send_sign_up_email(email, user_name, user_display_name):
    subject = "CIS Insight - アカウント登録完了"
    message = f"CIS Insightへの本登録が完了しました。\nアカウント登録内容は以下のとおりです。\n\nユーザー名: {user_name}\n表示名: {user_display_name}\nメールアドレス: {email}\n\n{SITE_URL}"
    send_mail(subject, message, EMAIL_HOST_USER, [email], fail_silently=False)
    return True

# ログインページ関連
def render_sign_in_page(request):
    return render(request, 'sign_in.html')

# ログイン関連
def sign_in(request):
    try:
        user_name = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        user = authenticate(request, username = user_name, password = password)
        
        if user is None:
            return JsonResponse({'status': "error", "message" : "ユーザー名またはパスワードが正しくありません。"})
        
        if remember_me == "on":
            request.session.set_expiry(1209600) # 2週間保持
        else:
            request.session.set_expiry(0)

        login(request, user)
        return JsonResponse({'status': "success"})
    except Exception as e:
        return JsonResponse({'status': "error", "message" : "ログインに失敗しました。", "error_message": str(e)})

# ログアウト関連
@login_required
def render_logout_page(request):
    return render(request, 'logout.html')

# ニュース設定ページ関連
@login_required
def render_news_settings_page(request):
    user = get_user_model().objects.get(pk=request.user.pk)
    return render(request, 'news_settings.html', {'user': user, 'cis_countries': CIS_COUNTRIES, 'topics': TOPICS})

@csrf_exempt
def news_settings(request):
    try:
        user = get_user_model().objects.get(pk=request.user.pk)
        countries = request.POST.getlist('countries')
        topics = request.POST.getlist('topics')
        user.user_news_referred_country = countries
        user.user_news_referred_topic = topics
        user.save()
        return JsonResponse({'status': "success"})
    except Exception as e:
        return JsonResponse({'status': "error", "message" : "ニュース設定に失敗しました。", "error_message": str(e)})

@login_required
def render_display_settings_page(request):
    return render(request, 'display_settings.html')

# アカウント設定ページ関連
@login_required
def render_account_settings_page(request):
    user = get_user_model().objects.get(pk=request.user.pk)
    return render(request, 'account_settings.html', {'user': user})

@csrf_exempt
def account_settings(request):
    try:
        user = get_user_model().objects.get(pk=request.user.pk)
        user_name = request.POST.get('user_name')
        user_display_name = request.POST.get('display_name')
        user_icon = request.FILES.get('icon')
        user_email = request.POST.get('email')

        if user_icon:
            if user.user_icon:
                user.user_icon.delete(save = False)

            new_user_icon_name = ''.join(random.choices(string.ascii_letters + string.digits, k = 128)) + '.png'
            user.user_icon.save(new_user_icon_name, user_icon, save = False)

        if user_name != user.user_name:
            return JsonResponse({'status': "error", "message" : "不正な入力です。"})

        if len(user_display_name) > 16:
            return JsonResponse({'status': "error", "message" : "表示名は16文字以内で入力してください。"})

        if user_email != user.user_email:
            if User.objects.is_user_email_duplicate(user_email):
                return JsonResponse({'status': "error", "message" : "既に別のアカウントで登録されているメールアドレスです。"})
            # else: TODO 新規メアドの認証後、DB更新するようにする
            #     send_account_settings_email(user_email, user_name, user_display_name)

        user.user_display_name = user_display_name
        user.user_email = user_email
        user.save()
        return JsonResponse({'status': "success"})
    except Exception as e:
        return JsonResponse({'status': "error", "message" : "アカウント設定に失敗しました。", "error_message": str(e)})

# パスワード変更ページ関連
@login_required
def render_password_change_page(request):
    return render(request, 'password_change.html')

# パスワード変更関連
@csrf_exempt
def password_change(request):
    try:
        user = get_user_model().objects.get(pk=request.user.pk)
        password = request.POST.get('password')
        user.set_password(password)
        user.save()
        return JsonResponse({'status': "success"})
    except Exception as e:
        return JsonResponse({'status': "error", "message" : "パスワード変更に失敗しました。", "error_message": str(e)})

# 管理者ページ関連
@login_required
def render_admin_page(request):
    if not request.user.is_staff:
        return render(request, 'error.html')
    return render(request, 'admin.html')