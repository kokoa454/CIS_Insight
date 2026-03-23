from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import feedparser
import logging
import re
from django.http import JsonResponse
import json
from django.db import transaction

from news.models import CisAndNeighborCountry, CisCountry, Topic, NewsRss, NewsArticle
from core.settings import MAXIMUM_COMPANY_LENGTH

logger = logging.getLogger(__name__)

# ダッシュボードページ関連
@login_required
def render_dashboard_page(request):
    user = request.user
    cis_countries = CisAndNeighborCountry.objects.all()
    topics = Topic.objects.all()

    user_news_referred_country = user.news_referred_country
    user_news_referred_topic = user.news_referred_topic

    if len(user_news_referred_country) > 0 and len(user_news_referred_topic) > 0:
        news_articles = NewsArticle.objects.filter(country__country_code__in = user_news_referred_country, topic__name_en__in = user_news_referred_topic, is_active = True).select_related('country', 'rss').prefetch_related('topic').distinct().order_by('-published_at')[:100]
    elif len(user_news_referred_country) > 0 and len(user_news_referred_topic) == 0:
        news_articles = NewsArticle.objects.filter(country__country_code__in = user_news_referred_country, is_active = True).select_related('country', 'rss').distinct().order_by('-published_at')[:100]
    elif len(user_news_referred_country) == 0 and len(user_news_referred_topic) > 0:
        news_articles = NewsArticle.objects.filter(topic__name_en__in = user_news_referred_topic, is_active = True).select_related('country', 'rss').prefetch_related('topic').distinct().order_by('-published_at')[:100]
    else:
        news_articles = []
    
    return render(request, 'dashboard.html', {'user': user, 'cis_countries': cis_countries, 'topics': topics, 'news_articles': news_articles})

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
    
    if country not in CisCountry.objects.all().values_list('country_code', flat = True):
        return JsonResponse({'status': "error", "message" : "国名が不正に入力されています。"})
    else:
        country = CisCountry.objects.get(country_code = country)

    if is_active not in ["on", "off"]:
        return JsonResponse({'status': "error", "message" : "有効/無効の値が不正に入力されています。"})
    
    if is_active == "on":
        is_active = True
    else:
        is_active = False

    if not test_rss(url):
        return JsonResponse({'status': "error", "message" : "RSSの取得テストに失敗しました。"})

    try:
        NewsRss.objects.get_or_create(
            url = url,
            defaults = {
                'company': company,
                'country': country,
                'is_active': is_active
            }
        )
        return JsonResponse({'status': "success", "message" : "RSS設定に成功しました。"})
    except Exception as e:
        logger.error(f'Exception in rss_settings: {e}')
        return JsonResponse({'status': "error", "message" : "RSS設定に失敗しました。", "error_message": str(e)})

def test_rss(url):
    try:
        feed = feedparser.parse(url)

        if len(feed.entries) == 0:
            return False
        
        return True
    except Exception as e:
        logger.error(f'Exception in test_rss: {e}')
        return False
    

@login_required
def delete_rss(request):
    try:
        data = json.loads(request.body)
        rss_id = data.get('rss_id')
        rss_is_active = data.get('rss_is_active')
        rss_company = data.get('rss_company')
        rss_url = data.get('rss_url')

        if rss_is_active == "True":
            rss_is_active = True
        else:
            rss_is_active = False
        
        rss = NewsRss.objects.get(pk = rss_id)

        if rss.is_active != rss_is_active or rss.company != rss_company or rss.url != rss_url:
            return JsonResponse({'status': "error", "message" : "不正な入力です。"})

        if rss.is_active == True:
            return JsonResponse({'status': "error", "message" : "RSS設定を削除するには、まず無効化してください。"})
        
        news_articles = NewsArticle.objects.filter(rss = rss)

        with transaction.atomic():
            for news_article in news_articles:
                if news_article.image is not None:
                    news_article.image.delete()
                news_article.delete()

            rss.delete()
        return JsonResponse({'status': "success", "message" : "RSS設定を削除しました。"})
    except Exception as e:
        logger.error(f'Exception in delete_rss: {e}')
        return JsonResponse({'status': "error", "message" : "RSS設定の削除に失敗しました。", "error_message": str(e)})

@login_required
def deactivate_rss(request):
    try:
        data = json.loads(request.body)
        rss_id = data.get('rss_id')
        rss_is_active = data.get('rss_is_active')
        rss_company = data.get('rss_company')
        rss_url = data.get('rss_url')
        
        rss = NewsRss.objects.get(pk = rss_id)

        if rss_is_active == "True":
            rss_is_active = True
        else:
            rss_is_active = False

        if rss.is_active != rss_is_active or rss.company != rss_company or rss.url != rss_url:
            return JsonResponse({'status': "error", "message" : "不正な入力です。"})
        
        with transaction.atomic():
            rss.is_active = False
            rss.save()
        return JsonResponse({'status': "success", "message" : "RSS設定を無効化しました。"})
    except Exception as e:
        logger.error(f'Exception in deactivate_rss: {e}')
        return JsonResponse({'status': "error", "message" : "RSS設定を無効化に失敗しました。", "error_message": str(e)})

@login_required
def activate_rss(request):
    try:
        data = json.loads(request.body)
        rss_id = data.get('rss_id')
        rss_is_active = data.get('rss_is_active')
        rss_company = data.get('rss_company')
        rss_url = data.get('rss_url')
        
        rss = NewsRss.objects.get(pk = rss_id)

        if rss_is_active == "True":
            rss_is_active = True
        else:
            rss_is_active = False

        if rss.is_active != rss_is_active or rss.company != rss_company or rss.url != rss_url:
            return JsonResponse({'status': "error", "message" : "不正な入力です。"})
        
        with transaction.atomic():
            rss.is_active = True
            rss.save()
        return JsonResponse({'status': "success", "message" : "RSS設定を有効化しました。"})
    except Exception as e:
        logger.error(f'Exception in activate_rss: {e}')
        return JsonResponse({'status': "error", "message" : "RSS設定を有効化に失敗しました。", "error_message": str(e)})
