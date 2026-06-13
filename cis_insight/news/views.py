import json
import logging
import re
import time

import feedparser
import trafilatura
from core.exceptions import (RateLimitError, ServerError,
                             convert_to_custom_ai_exception)
from core.settings import (DEFAULT_HEADERS, GEMINI_API_KEY_1, GEMINI_API_KEY_2,
                           GEMINI_API_KEY_3, GEMINI_API_KEY_4,
                           GEMINI_API_KEY_5, GEMINI_API_KEY_6,
                           GEMINI_API_KEY_7, GEMINI_API_KEY_8,
                           GEMINI_API_KEY_9, GEMINI_API_KEY_10, GEMINI_MODEL_1,
                           GEMINI_MODEL_2, GEMINI_MODEL_3, GEMINI_MODEL_4,
                           GEMINI_MODEL_5, GEMINI_MODEL_6, GEMINI_MODEL_7,
                           IMPERSONATE_TARGET, MAXIMUM_COMPANY_LENGTH)
from core.utils import is_safe_url
from core.views import render_error_page
from curl_cffi import requests
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from google import genai
from news.models import (CisAndNeighborCountry, CisCountry, NewsArticle,
                         NewsRss, Topic)

logger = logging.getLogger(__name__)

# ダッシュボードページ関連
def get_news_filter(user):
    user_news_referred_country = user.news_referred_country
    user_news_referred_topic = user.news_referred_topic

    news_filter = Q(is_active = True)

    if user_news_referred_country and user_news_referred_topic:
        news_filter &= Q(country__country_code__in = user_news_referred_country, topic__name_en__in = user_news_referred_topic)
    elif user_news_referred_country:
        news_filter &= Q(country__country_code__in = user_news_referred_country)
    elif user_news_referred_topic:
        news_filter &= Q(topic__name_en__in = user_news_referred_topic)
    return news_filter

@never_cache
def get_user_news_count(request):
    return JsonResponse({'read_count': request.user.news_count})

@login_required
def render_dashboard_page(request):
    user = request.user
    cis_countries = cache.get_or_set('cis_neighbor_countries', lambda: list(CisAndNeighborCountry.objects.all()), 3600)
    topics = cache.get_or_set('news_topics', lambda: list(Topic.objects.all()), 3600)

    news_filter = get_news_filter(user)
    news_articles = NewsArticle.objects.filter(news_filter).only('title_ru', 'title_ja', 'published_at', 'image', 'country').select_related('country').prefetch_related('topic').order_by('-published_at').distinct()[:10]
    
    return render(request, 'dashboard.html', {'user': user, 'cis_countries': cis_countries, 'topics': topics, 'news_articles': news_articles})

@login_required
def load_more_news_articles(request):
    time.sleep(0.5)
    page = int(request.GET.get('page', 2))
    
    news_filter = get_news_filter(request.user)
    
    news_articles = NewsArticle.objects.filter(news_filter).only('title_ru', 'title_ja', 'published_at', 'image', 'country').select_related('country').prefetch_related('topic').order_by('-published_at').distinct()
    paginator = Paginator(news_articles, 10)
    
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'html': '', 'has_next': False})

    html = render_to_string('includes/news_article_list.html', {'news_articles': page_obj.object_list})
    return JsonResponse({'html': html, 'has_next': page_obj.has_next()})

# ニュース記事関連
@login_required
def render_news_article_page(request, pk):
    user = request.user
    cis_countries = cache.get_or_set('cis_neighbor_countries', lambda: list(CisAndNeighborCountry.objects.all()), 3600)
    topics = cache.get_or_set('news_topics', lambda: list(Topic.objects.all()), 3600)

    try:
        news_article = NewsArticle.objects.get(pk = pk, is_active = True)

        with transaction.atomic():
            user.news_count += 1
            user.save()

        with transaction.atomic():
            news_article.read_count += 1
            news_article.save()
    except ObjectDoesNotExist:
        return render_error_page(request, '404', 'Page not found')
    
    return render(request, 'news_article.html', {'user': user, 'cis_countries': cis_countries, 'topics': topics, 'news_article': news_article})

@login_required
def get_news_article_content(request, pk):
    try:
        news_article = NewsArticle.objects.select_related('country', 'rss').get(pk = pk)

        if news_article.is_active == False:
            return JsonResponse({'error': 'Article is not active'}, status=403)
        
        if news_article.is_content_added == False:

            try:
                if not is_safe_url(news_article.url):
                    return JsonResponse({'error': 'Invalid URL'}, status=400)

                downloaded = requests.get(news_article.url, headers = DEFAULT_HEADERS, impersonate = IMPERSONATE_TARGET)
                downloaded.raise_for_status()
                article_content = trafilatura.extract(downloaded.text)
                
                if article_content is None or len(article_content) == 0:
                    return JsonResponse({'error': 'Failed to fetch content'}, status=500)
                
                cleaned_article_content = clean_article_content(article_content, news_article.rss)
                if cleaned_article_content is None or len(cleaned_article_content) == 0:
                    return JsonResponse({'error': 'Failed to clean content'}, status=500)
                
                content_ru = cleaned_article_content
            except Exception as e:
                logger.error(f'Exception in get_news_article_content: {e}')
                content_ru = None

            if content_ru is None:
                return JsonResponse({'error': 'Failed to fetch content'}, status=500)
            news_article.content_ru = content_ru
            news_article.is_content_added = True
            
            try:
                with transaction.atomic():
                    news_article.save()
            except Exception as e:
                logger.error(f'Exception in get_news_article: {e}')
                return JsonResponse({'error': 'Database save failed'}, status=500)

        return JsonResponse({'content_ru': news_article.content_ru})
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Article not found'}, status=404)

@login_required
def get_news_article_translated_content(request, pk):
    try:
        news_article = NewsArticle.objects.select_related('country', 'rss').get(pk = pk)

        if news_article.is_active == False:
            return JsonResponse({'error': 'Article is not active'}, status=403)

        if news_article.is_content_translated == False:
            content_ja = translate_content(news_article.content_ru, news_article.rss)
            if content_ja is None:
                return JsonResponse({'error': 'Failed to translate content'}, status=500)
            news_article.content_ja = content_ja
            news_article.is_content_translated = True
            try:
                with transaction.atomic():
                    news_article.save()
            except Exception as e:
                logger.error(f'Exception in get_news_article_translated_content: {e}')
                news_article.rss.last_error = f"{e} while translating content"
                news_article.rss.save()
                return JsonResponse({'error': 'Database save failed'}, status=500)

        return JsonResponse({'content_ja': news_article.content_ja})
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Article not found'}, status=404)

def clean_article_content(article_content, rss):
    prompt = f"""
    Clean the following Russian news content.
    - Extract ONLY the core narrative text.
    - Remove the dateline (e.g., "CITY, Date - Agency Name").
    - Remove all noise: ads, social media links, navigation menu, phone numbers, emails, and copyright notices.
    - Remove repetitive titles or image captions.
    - Output ONLY the plain text. 
    - Do not add any extra empty lines or spaces at the beginning or end of the output.
    - Separate each paragraph with a double newline (\n\n).

    Content: {article_content}
    """

    for api_key in [GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3, GEMINI_API_KEY_4, GEMINI_API_KEY_5, GEMINI_API_KEY_6, GEMINI_API_KEY_7, GEMINI_API_KEY_8, GEMINI_API_KEY_9, GEMINI_API_KEY_10]:
        client = genai.Client(api_key = api_key)
        models = [GEMINI_MODEL_1, GEMINI_MODEL_2, GEMINI_MODEL_3, GEMINI_MODEL_4, GEMINI_MODEL_5, GEMINI_MODEL_6, GEMINI_MODEL_7]

        for model in models:
            try:
                response = client.models.generate_content(
                    model = model,
                    contents = prompt,
                )

                return response.text.strip()
            except Exception as e:
                error = convert_to_custom_ai_exception(e)
                if isinstance(error, RateLimitError) or isinstance(error, ServerError):
                    continue

                logger.error(f"Error for model {model}: {e}")
                rss.last_error = f"{error.user_message} while cleaning content"
                rss.save()
                continue
                
    return None

def translate_content(content_ru, rss):
    prompt = f"""
    Translate the following Russian news content into natural Japanese for a news site.
    - Do not add extra explanations.
    - Translate all the words into officially correct Japanese(である調).
    - If media company name or organization name, person name or place name are included in the content, translate them into officially correct Japanese.
    - Return only the translated content.

    Content: {content_ru}
    """

    for api_key in [GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3, GEMINI_API_KEY_4, GEMINI_API_KEY_5, GEMINI_API_KEY_6, GEMINI_API_KEY_7, GEMINI_API_KEY_8, GEMINI_API_KEY_9, GEMINI_API_KEY_10]:
        client = genai.Client(api_key = api_key)
        models = [GEMINI_MODEL_1, GEMINI_MODEL_2, GEMINI_MODEL_3, GEMINI_MODEL_4, GEMINI_MODEL_5, GEMINI_MODEL_6, GEMINI_MODEL_7]

        for model in models:
            try:
                response = client.models.generate_content(
                    model = model,
                    contents = prompt,
                )
                
                return response.text.strip()
            except Exception as e:
                error = convert_to_custom_ai_exception(e)
                if isinstance(error, RateLimitError) or isinstance(error, ServerError):
                    continue
                
                logger.error(f"Error for model {model}: {e}")
                rss.last_error = f"{error.user_message} while translating content"
                rss.save()
                continue
                
    return None

# RSS設定ページ関連
@login_required
@user_passes_test(lambda user: user.is_staff)
def render_rss_settings_page(request):
    countries = CisCountry.objects.all()
    rsses = NewsRss.objects.all()
    return render(request, 'rss_settings.html', {'countries': countries, 'rsses': rsses})

@login_required
@user_passes_test(lambda user: user.is_staff)
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
    if not is_safe_url(url):
        return False
    
    try:
        downloaded = requests.get(url, headers = DEFAULT_HEADERS, impersonate = IMPERSONATE_TARGET)
        downloaded.raise_for_status()
        
        feed = feedparser.parse(downloaded.content)

        if len(feed.entries) == 0:
            return False
        
        return True
    except Exception as e:
        logger.error(f'Exception in test_rss: {e}')
        return False
    

@login_required
@user_passes_test(lambda user: user.is_staff)
def delete_rss(request):
    try:
        data = json.loads(request.body)
        rss_id = data.get('rss_id')
        rss_company = data.get('rss_company')
        rss_url = data.get('rss_url')
        
        rss = NewsRss.objects.get(pk = rss_id)

        if rss.company != rss_company or rss.url != rss_url:
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
@user_passes_test(lambda user: user.is_staff)
def delete_rss_error(request):
    try:
        data = json.loads(request.body)
        rss_id = data.get('rss_id')
        rss_company = data.get('rss_company')
        rss_url = data.get('rss_url')
        
        rss = NewsRss.objects.get(pk = rss_id)

        if rss.company != rss_company or rss.url != rss_url:
            return JsonResponse({'status': "error", "message" : "不正な入力です。"})
        
        with transaction.atomic():
            rss.last_error = None
            rss.save()
        return JsonResponse({'status': "success", "message" : "RSSエラーメッセージを削除しました。"})
    except Exception as e:
        logger.error(f'Exception in delete_rss_error: {e}')
        return JsonResponse({'status': "error", "message" : "RSSエラーメッセージの削除に失敗しました。", "error_message": str(e)})

@login_required
@user_passes_test(lambda user: user.is_staff)
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
@user_passes_test(lambda user: user.is_staff)
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
