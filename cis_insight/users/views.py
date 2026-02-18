from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django_ratelimit.decorators import ratelimit
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect
import re
import random
import string
import secrets
import logging
import json
from PIL import Image
from io import BytesIO
import sys

from .models import PreUser
from .models import User
from .models import EmailChange
from news.models import (CisCountry, Topic)
from core.settings import (SITE_URL, EMAIL_HOST_USER, MAXIMUM_USERNAME_LENGTH, MAXIMUM_DISPLAY_NAME_LENGTH, MINIMUM_PASSWORD_LENGTH, MAXIMUM_EMAIL_LENGTH, VALIDATION_CODE_LENGTH, EMAIL_CHANGE_EXPIRATION_TIME_MINUTES, MAXIMUM_ICON_SIZE_PIXEL)

logger = logging.getLogger(__name__)

# 共通
def generate_verification_code():
    return secrets.token_hex(VALIDATION_CODE_LENGTH)

# ユーザ登録ページ関連
def render_sign_up_page(request, verification_code):
    try:
        pre_user = PreUser.objects.get(verification_code = verification_code)
    except PreUser.DoesNotExist:
        return render(request, 'error.html')

    if not pre_user.is_expired:
        user_email = pre_user.email
        return render(request, 'sign_up.html', {'user_email': user_email, 'verification_code': verification_code})
    else:
        return render(request, 'error.html')

def sign_up(request):
    try:
        email = request.POST.get('email')
        username = request.POST.get('username')
        display_name = request.POST.get('display_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        verification_code = request.POST.get('verification_code')
        
        if len(email) > MAXIMUM_EMAIL_LENGTH:
            return JsonResponse({'status': "error", "message" : "メールアドレスが不正に入力されています。"})
        
        if User.objects.filter(email = email).exists():
            return JsonResponse({'status': "error", "message" : "すでに登録済みのメールアドレスです。"})
        
        if User.objects.filter(username = username).exists():
            return JsonResponse({'status': "error", "message" : "ユーザー名が他のユーザーと重複しています。"})

        pre_user = PreUser.objects.get_pre_user(verification_code)
        if pre_user.is_expired:
            return JsonResponse({'status': "error", "message" : "リンクの有効期限が切れています。"})
        
        registered_email = pre_user.email
        if registered_email != email:
            return JsonResponse({'status': "error", "message" : "登録済みのメールアドレスと一致しません。"})

        if len(username) > MAXIMUM_USERNAME_LENGTH:
            return JsonResponse({'status': "error", "message" : "ユーザー名は" + str(MAXIMUM_USERNAME_LENGTH) + "文字以内で入力してください。"})

        if not re.match(r'^[a-z0-9_]+$', username):
            return JsonResponse({'status': "error", "message" : "ユーザー名は小文字英数字またはアンダースコアのみ使用できます。"})
        
        if len(display_name) > MAXIMUM_DISPLAY_NAME_LENGTH:
            return JsonResponse({'status': "error", "message" : "表示名は" + str(MAXIMUM_DISPLAY_NAME_LENGTH) + "文字以内で入力してください。"})
        
        if len(password) < MINIMUM_PASSWORD_LENGTH:
            return JsonResponse({'status': "error", "message" : "パスワードは" + str(MINIMUM_PASSWORD_LENGTH) + "文字以上で入力してください。"})

        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).*$', password):
            return JsonResponse({'status': "error", "message" : "パスワードは大小英数字混合で入力してください。"})

        if password != password_confirm:
            return JsonResponse({'status': "error", "message" : "パスワードが一致しません。"})

        with transaction.atomic():
            user = User.objects.create_user(username, email, display_name, password)

            pre_user.delete()
            logger.info(f'PreUser {username} deleted successfully')

        login(request, user)
        
        if not send_sign_up_email(email, username, display_name):
            return JsonResponse({'status': "error", "message" : "メールの送信に失敗しました。時間を空けてから再度お試しください。"})

        return JsonResponse({'status': "success"})
    except Exception as e:
        logger.error(f'Exception in sign_up with user_name: {username}: {e}')
        return JsonResponse({'status': "error", "message" : "登録に失敗しました。", "error_message": str(e)})

def send_sign_up_email(email, username, display_name):
    try:
        subject = "CIS Insight - アカウント登録完了"
        message = f"CIS Insightへの本登録が完了しました。\nアカウント登録内容は以下のとおりです。\n\nユーザー名: {username}\n表示名: {display_name}\nメールアドレス: {email}\n\n{SITE_URL}"
        send_mail(subject, message, EMAIL_HOST_USER, [email], fail_silently=False)
        logger.info(f'Email sent to: {email}')
        return True
    except Exception as e:
        logger.error(f'Exception in send_sign_up_email: {e}')
        return False

# ログインページ関連
def render_sign_in_page(request):
    return render(request, 'sign_in.html')

def sign_in(request):
    try:
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        user = authenticate(request, username = username, password = password)
        
        if user is None:
            return JsonResponse({'status': "error", "message" : "ユーザー名またはパスワードが正しくありません。"})
        
        if remember_me == "on":
            request.session.set_expiry(1209600) # 2週間保持
        else:
            request.session.set_expiry(0)

        login(request, user)
        return JsonResponse({'status': "success"})
    except Exception as e:
        logger.error(f'Exception in sign_in: {e}')
        return JsonResponse({'status': "error", "message" : "ログインに失敗しました。", "error_message": str(e)})

# ログアウトページ関連
def render_logout_complete_page(request):
    return render(request, 'logout_complete.html')

@login_required
def logout(request):
    auth_logout(request)
    return redirect('logout_complete')

# ニュース設定ページ関連
@login_required
def render_news_settings_page(request):
    user = get_user_model().objects.get(pk = request.user.pk)
    cis_countries = CisCountry.objects.all()
    topics = Topic.objects.all()
    return render(request, 'news_settings.html', {'user': user, 'cis_countries': cis_countries, 'topics': topics})

@login_required
@ratelimit(key = 'ip', rate = '5/m', block = True)
def news_settings(request):
    try:
        user = get_user_model().objects.get(pk = request.user.pk)
        countries = request.POST.getlist('countries')
        topics = request.POST.getlist('topics')

        with transaction.atomic():
            user.news_referred_country = countries
            user.news_referred_topic = topics
            user.save()
        return JsonResponse({'status': "success"})
    except Exception as e:
        logger.error(f'Exception in news_settings: {e}')
        return JsonResponse({'status': "error", "message" : "ニュース設定に失敗しました。", "error_message": str(e)})

# 表示設定ページ関連
@login_required
def render_display_settings_page(request):
    return render(request, 'display_settings.html')

# アカウント設定ページ関連
@login_required
def render_account_settings_page(request):
    user = get_user_model().objects.get(pk=request.user.pk)
    return render(request, 'account_settings.html', {'user': user})

@login_required
@ratelimit(key = 'ip', rate = '5/m', block = True)
def account_settings(request):
    try:
        user = get_user_model().objects.get(pk = request.user.pk)
        username = request.POST.get('username')
        display_name = request.POST.get('display_name')
        email = request.POST.get('email')
        icon = request.FILES.get('icon')

        if icon:
            if user.icon:
                with transaction.atomic():
                    user.icon.delete(save = False)
                    new_icon_name = ''.join(random.choices(string.ascii_letters + string.digits, k = 128)) + '.png'
                    icon = enhance_icon(icon, new_icon_name)
                    user.icon.save(new_icon_name, icon, save = False)

        if username != user.username:
            return JsonResponse({'status': "error", "message" : "不正な入力です"})

        if len(display_name) > MAXIMUM_DISPLAY_NAME_LENGTH:
            return JsonResponse({'status': "error", "message" : f"表示名は {MAXIMUM_DISPLAY_NAME_LENGTH}文字以内で入力してください。"})

        if email != user.email:
            return JsonResponse({'status': "error", "message" : "不正な入力です"})

        with transaction.atomic():
            user.display_name = display_name
            user.save()
        return JsonResponse({'status': "success"})
    except Exception as e:
        print(e)
        logger.error(f'Exception in account_settings: {e}')
        return JsonResponse({'status': "error", "message" : "アカウント設定に失敗しました。", "error_message": str(e)})

def enhance_icon(icon, icon_name, size = MAXIMUM_ICON_SIZE_PIXEL):
    icon = Image.open(icon)
    icon = icon.convert("RGBA")

    w, h = icon.size
    target_w, target_h = size

    scale = max(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    icon = icon.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h
    icon = icon.crop((left, top, right, bottom))

    buffer = BytesIO()
    icon.save(buffer, format="PNG")
    buffer.seek(0)

    return InMemoryUploadedFile(buffer, None, icon_name, 'image/png', sys.getsizeof(buffer), None)

@login_required
@ratelimit(key = 'ip', rate = '5/m', block = True)
def pre_email_change(request):
    try:
        data = json.loads(request.body)
        user = get_user_model().objects.get(pk = request.user.pk)
        old_email = user.email
        new_email = data.get('email')
        verification_code = generate_verification_code()

        try:
            validate_email(new_email)
        except ValidationError:
            logger.error(f'Invalid email format: {new_email}')
            return JsonResponse({'status': 'error', 'message': 'メールアドレスの形式が正しくありません。'})
        
        if User.objects.filter(email = new_email).exists():
            return JsonResponse({'status': "error", "message" : "既に別のアカウントで登録されているメールアドレスです。"})
        
        if old_email == new_email:
            return JsonResponse({'status': "error", "message" : "新しいメールアドレスは現在のメールアドレスと異なる必要があります。"})

        if EmailChange.objects.filter(user = user).exists() or EmailChange.objects.filter(new_email = new_email).exists():
            return JsonResponse({'status': "error", "message" : "既にメールアドレスの変更用リンクが送信されています。"})
        
        EmailChange.objects.create_email_change(user, verification_code, new_email)
        
        if not send_email_change_email(new_email, user.username, user.display_name, verification_code):
            return JsonResponse({'status': "error", "message" : "メールアドレスの変更用リンクの送信に失敗しました。"})
        
        return JsonResponse({'status': "success"})
    except Exception as e:
        logger.error(f'Exception in pre_email_change: {e}')
        return JsonResponse({'status': "error", "message" : "メールアドレスの変更用リンクの送信に失敗しました。", "error_message": str(e)})

def send_email_change_email(email, username, display_name, verification_code):
    try:
        subject = "CIS Insight - メールアドレス変更"
        message = f"下記の内容でメールアドレス変更を受け付けました。\n\nユーザー名: {username}\n表示名: {display_name}\n新しいメールアドレス: {email}\n\n以下のリンクでメールアドレス変更を完了してください。\n有効期限は{EMAIL_CHANGE_EXPIRATION_TIME_MINUTES}分です。なお、このメールは自動送信のため、返信はできません。\n\n{SITE_URL}/email_change/{verification_code}"
        send_mail(subject, message, EMAIL_HOST_USER, [email], fail_silently=False)
        return True
    except Exception as e:
        logger.error(f'Exception in send_email_change_email: {e}')
        return False

def render_email_change_page(request, verification_code):
    try:
        email_change = EmailChange.objects.get(verification_code = verification_code)
    except EmailChange.DoesNotExist:
        return render(request, 'error.html')

    if not email_change.is_expired:
        user = get_user_model().objects.get(pk = email_change.user.pk)
        user.email = email_change.new_email
        
        with transaction.atomic():
            user.save()
            email_change.delete()
        
        return render(request, 'email_change.html')
    else:
        return render(request, 'error.html')

# パスワード変更関連
@login_required
@ratelimit(key = 'ip', rate = '5/m', block = True)
def password_change(request):
    try:
        user = get_user_model().objects.get(pk = request.user.pk)
        old_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')
        
        if not user.check_password(old_password):
            return JsonResponse({'status': "error", "message" : "現在のパスワードが正しくありません。"})
        
        if new_password != new_password_confirm:
            return JsonResponse({'status': "error", "message" : "新しいパスワードと確認用パスワードが一致しません。"})
        
        if new_password == old_password:
            return JsonResponse({'status': "error", "message" : "新しいパスワードは現在のパスワードと同じです。"})
        
        if len(new_password) < MINIMUM_PASSWORD_LENGTH:
            return JsonResponse({'status': "error", "message" : "新しいパスワードは8文字以上で入力してください。"})
        
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).*$', new_password):
            return JsonResponse({'status': "error", "message" : "パスワードは大小英数字混合で入力してください。"})
        
        with transaction.atomic():
            user.set_password(new_password)
            user.save()
            
        return JsonResponse({'status': "success"})
    except Exception as e:
        logger.error(f'Exception in password_change: {e}')
        return JsonResponse({'status': "error", "message" : "パスワードの変更に失敗しました。", "error_message": str(e)})
