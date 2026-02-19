from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
import feedparser
import logging
import re
from django.http import JsonResponse

from news.models import CisAndNeighborCountry, CisCountry, Topic, NewsRss
from core.settings import MAXIMUM_COMPANY_LENGTH

logger = logging.getLogger(__name__)

# ダッシュボードページ関連
@login_required
def render_dashboard_page(request):
    user = get_user_model().objects.get(pk=request.user.pk)
    cis_countries = CisAndNeighborCountry.objects.all()
    topics = Topic.objects.all()
    return render(request, 'dashboard.html', {'user': user, 'cis_countries': cis_countries, 'topics': topics})

# RSS設定ページ関連
@login_required
def render_rss_settings_page(request):
    countries = CisCountry.objects.all()
    rsses = NewsRss.objects.all()
    return render(request, 'rss_settings.html', {'countries': countries, 'rsses': rsses})

@login_required
def rss_settings(request):
    company = request.POST.get('company')
    country = request.POST.get('country')
    url = request.POST.get('url')
    is_active = request.POST.get('is_active')

    if NewsRss.objects.filter(url = url).exists():
        return JsonResponse({'status': "error", "message" : "すでに登録済みのURLです。"})

    if not re.match(r'^https?:\/\/.+$', url):
        return JsonResponse({'status': "error", "message" : "URLが不正に入力されています。"})
    
    if len(company) > MAXIMUM_COMPANY_LENGTH:
        return JsonResponse({'status': "error", "message" : "会社名は" + str(MAXIMUM_COMPANY_LENGTH) + "文字以内で入力してください。"})
    
    if country not in CisCountry.objects.all().values_list('country_code', flat=True):
        return JsonResponse({'status': "error", "message" : "国名が不正に入力されています。"})
    else:
        country = CisCountry.objects.get(country_code = country)

    if is_active not in ["on", "off"]:
        return JsonResponse({'status': "error", "message" : "有効/無効の値が不正に入力されています。"})
    
    if is_active == "on":
        is_active = True
    else:
        is_active = False

    try:
        NewsRss.objects.create_news_rss(company, url, country, is_active)
        return JsonResponse({'status': "success", "message" : "RSS設定に成功しました。"})
    except Exception as e:
        print(e)
        logger.error(f'Exception in rss_settings: {e}')
        return JsonResponse({'status': "error", "message" : "RSS設定に失敗しました。", "error_message": str(e)}) 
