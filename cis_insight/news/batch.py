import datetime
import logging
import random
import string
import sys
import time
from datetime import timedelta
from io import BytesIO

import feedparser
import newspaper
import requests
import trafilatura
from core.exceptions import RateLimitError, convert_to_custom_ai_exception
from core.settings import (ALLOWED_IMAGE_SIZE, ALLOWED_IMAGE_TYPE, CHUNK_SIZE,
                           DISPLAY_DAY_LIMIT, GEMINI_API_KEY_1,
                           GEMINI_API_KEY_2, GEMINI_API_KEY_3,
                           GEMINI_API_KEY_4, GEMINI_API_KEY_5,
                           GEMINI_API_KEY_6, GEMINI_API_KEY_7,
                           GEMINI_API_KEY_8, GEMINI_API_KEY_9,
                           GEMINI_API_KEY_10, GEMINI_MODEL_1, GEMINI_MODEL_2,
                           GEMINI_MODEL_3, GEMINI_MODEL_4, GEMINI_MODEL_5,
                           GEMINI_MODEL_6, GEMINI_MODEL_7, GROQ_API_KEY,
                           GROQ_MODEL_1, GROQ_MODEL_2, GROQ_MODEL_3,
                           MAXIMUM_IMAGE_SIZE_PIXEL)
from core.utils import is_safe_url
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from google import genai
from groq import Groq
from news.views import clean_article_content
from PIL import Image

from .models import NewsArticle, NewsRss, Topic

logger = logging.getLogger(__name__)

# TODO: RateLimitエラーなどのAPI提供側のエラーはエラーとして記録しないようにしたい

# Webサイト用
def fetch_web_news_articles():
    all_topics = list(Topic.objects.all())

    headers = {
        'User-Agent': 'Mozilla/5.0 ...',
        'Accept': 'application/rss+xml, ...'
    }

    for rss in NewsRss.objects.filter(is_active=True).order_by(F('last_fetched_at').asc(nulls_first=True)):
        processed_urls = set()

        try:
            downloaded = requests.get(rss.url, headers=headers)
            downloaded.raise_for_status()

            feed = feedparser.parse(downloaded.content)

            existing_articles = {
                a.url: a
                for a in NewsArticle.objects.filter(
                    url__in=[entry.link for entry in feed.entries if 'link' in entry]
                ).prefetch_related('topic')
            }

            completed_urls = {url for url, a in existing_articles.items() if a.is_active}

            for idx, entry in enumerate(feed.entries):
                try:
                    if idx % 5 == 0:
                        rss.refresh_from_db()
                        if rss.is_active == False:
                            break
                except ObjectDoesNotExist:
                    break

                if 'link' not in entry or 'title' not in entry:
                    continue

                url = entry.link

                if url in processed_urls or url in completed_urls:
                    continue

                if not is_safe_url(url):
                    logger.warning(f'SSRF prevention triggered: Blocked URL pointing to internal IP {url}')
                    continue

                processed_urls.add(url)

                existing_article = existing_articles.get(url)

                title_ru = entry.title

                if existing_article and existing_article.is_topic_picked:
                    topic = list(existing_article.topic.all())
                    topic_changed = False
                else:
                    topic = pick_up_news_article_topic(title_ru, all_topics, rss)
                    if topic is None:
                        continue
                    topic_changed = True

                if existing_article and existing_article.is_title_translated:
                    title_ja = existing_article.title_ja
                else:
                    title_ja = translate_title(title_ru, rss)
                    if title_ja is None:
                        continue

                if 'published_parsed' in entry:
                    published_at = timezone.make_aware(
                        datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed)),
                        datetime.timezone.utc
                    )
                else:
                    published_at = None

                if existing_article and existing_article.image:
                    image = None
                else:
                    if 'enclosures' in entry and len(entry.enclosures) > 0:
                        image_url = entry.enclosures[0].href
                    elif 'media_content' in entry and len(entry.media_content) > 0:
                        image_url = entry.media_content[0]['url']
                    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                        image_url = entry.media_thumbnail[0]['url']
                    else:
                        image_url = None

                    if image_url is not None:
                        if not is_safe_url(image_url):
                            logger.warning(f'SSRF prevention triggered: Blocked URL pointing to internal IP {image_url}')
                            image = None
                        else:
                            try:
                                image = download_image_from_rss(image_url)
                            except Exception as e:
                                image = None
                    else:
                        try:
                            image = download_image_from_article(url)
                        except Exception as e:
                            image = None

                if existing_article and existing_article.is_content_added:
                    content_ru = existing_article.content_ru
                    is_content_added = True
                else:
                    content_ru = get_news_article_content(rss, url)
                    is_content_added = content_ru is not None

                country = rss.country

                is_title_added = True if title_ru is not None else False
                is_title_translated = True if title_ja is not None else False
                is_topic_picked = True if topic is not None else False
                is_active = is_title_added and is_title_translated and is_topic_picked

                article_data ={
                    "url": url,
                    "title_ru": title_ru,
                    "title_ja": title_ja,
                    "published_at": published_at,
                    "country": country,
                    "image": image,
                    "rss": rss,
                    "content_ru": content_ru,
                    "is_active": is_active,
                    "is_title_added": is_title_added,
                    "is_title_translated": is_title_translated,
                    "is_topic_picked": is_topic_picked,
                    "is_content_added": is_content_added,
                }

                try:
                    with transaction.atomic():
                        if existing_article:
                            existing_article.title_ru = article_data['title_ru']
                            existing_article.title_ja = article_data['title_ja']
                            existing_article.published_at = article_data['published_at']
                            existing_article.country = article_data['country']
                            existing_article.is_active = article_data['is_active']
                            existing_article.is_title_added = article_data['is_title_added']
                            existing_article.is_title_translated = article_data['is_title_translated']
                            existing_article.is_topic_picked = article_data['is_topic_picked']

                            if not existing_article.is_content_added and article_data['is_content_added']:
                                existing_article.content_ru = article_data['content_ru']
                                existing_article.is_content_added = True

                            if article_data['image']:
                                existing_article.image = article_data['image']

                            existing_article.save()

                            if topic_changed:
                                existing_article.topic.set(topic)
                        else:
                            news_article, created = NewsArticle.objects.get_or_create(
                                url = url,
                                defaults={
                                    'title_ru': article_data['title_ru'],
                                    'title_ja': article_data['title_ja'],
                                    'published_at': article_data['published_at'],
                                    'country': article_data['country'],
                                    'image': article_data['image'],
                                    'rss': article_data['rss'],
                                    'content_ru': article_data['content_ru'],
                                    'is_active': article_data['is_active'],
                                    'is_title_added': article_data['is_title_added'],
                                    'is_title_translated': article_data['is_title_translated'],
                                    'is_topic_picked': article_data['is_topic_picked'],
                                    'is_content_added': article_data['is_content_added'],
                                }
                            )
                            if created:
                                news_article.topic.set(topic)

                except Exception as e:
                    logger.warning(f'Failed to save article {url}: {e}')
                    continue

            rss.total_articles = NewsArticle.objects.filter(rss=rss).count()
            rss.last_fetched_at = timezone.now()
            rss.save()

        except Exception as e:
            logger.error(f'Error fetching news articles from {rss.url}: {e}')
            rss.last_error = e
            rss.save()

def download_image_from_rss(image_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    if not (image_url is not None and (image_url.startswith('http://') or image_url.startswith('https://'))):
        logger.warning(f'Invalid image URL: {image_url}')
        return None

    try:
        with requests.get(image_url, headers = headers, stream = True, timeout=10) as image_data:
            if image_data is None or image_data.status_code != 200:
                return None

            content_type = image_data.headers.get('Content-Type', '').lower().split(';')[0].strip()

            if not any(content_type.startswith(t) for t in ALLOWED_IMAGE_TYPE):
                return None

            try:
                image_size = int(image_data.headers.get('Content-Length') or 0)
            except Exception:
                image_size = 0

            if image_size and image_size > ALLOWED_IMAGE_SIZE:
                return None

            buffer = BytesIO()
            downloaded_size = 0

            for chunk in image_data.iter_content(chunk_size = CHUNK_SIZE):
                if not chunk:
                    break
                downloaded_size += len(chunk)

                if downloaded_size > ALLOWED_IMAGE_SIZE:
                    return None

                buffer.write(chunk)

            buffer.seek(0)

            try:
                with Image.open(buffer) as img:
                    img.verify()

                buffer.seek(0)
            except Exception as e:
                logger.warning(f'Malicious or corrupt image from {image_url}: {e}')
                return None

            image_name = ''.join(random.choices(string.ascii_letters + string.digits, k = 64)) + '.png'
            image = enhance_image(buffer, image_name)

            return image
    except Exception as e:
        logger.error(f'Error enhancing image from {image_url}: {e}')
        return None

def download_image_from_article(url):
    if not (url is not None and (url.startswith('http://') or url.startswith('https://'))):
        logger.warning(f'Invalid article URL: {url}')
        return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }

    try:
        article = newspaper.Article(url)
        article.download()
        article.parse()

        image_url = article.top_image

        if not image_url:
            return None

        if not is_safe_url(image_url):
            logger.warning(f'SSRF prevention triggered: Blocked URL pointing to internal IP {image_url}')
            return None

        with requests.get(image_url, headers = headers, stream = True, timeout=10) as image_data:
            if image_data is None or image_data.status_code != 200:
                return None

            content_type = image_data.headers.get('Content-Type', '').lower().split(';')[0].strip()

            if not any(content_type.startswith(t) for t in ALLOWED_IMAGE_TYPE):
                return None

            try:
                image_size = int(image_data.headers.get('Content-Length') or 0)
            except Exception:
                image_size = 0

            if image_size and image_size > ALLOWED_IMAGE_SIZE:
                return None

            buffer = BytesIO()
            downloaded_size = 0

            for chunk in image_data.iter_content(chunk_size = CHUNK_SIZE):
                if not chunk:
                    break
                downloaded_size += len(chunk)

                if downloaded_size > ALLOWED_IMAGE_SIZE:
                    return None

                buffer.write(chunk)

            buffer.seek(0)

            try:
                with Image.open(buffer) as img:
                    img.verify()

                buffer.seek(0)
            except Exception as e:
                logger.warning(f'Malicious or corrupt image from {image_url}: {e}')
                return None

            image_name = ''.join(random.choices(string.ascii_letters + string.digits, k = 64)) + '.png'
            image = enhance_image(buffer, image_name)

            return image
    except Exception as e:
        logger.warning(f'Error downloading image from article {url}: {e}')
        return None

def enhance_image(image, image_name, size = MAXIMUM_IMAGE_SIZE_PIXEL):
    with Image.open(image) as src_img:
        img = src_img.convert("RGBA")

    w, h = img.size
    target_w, target_h = size

    scale = max(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h
    img = img.crop((left, top, right, bottom))

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    size_bytes = buffer.getbuffer().nbytes

    return InMemoryUploadedFile(buffer, None, image_name, 'image/png', size_bytes, None)

# Telegram用
def fetch_telegram_news_articles():
    #TODO テレグラム用の取得を実装
    pass

# 共通
def translate_title(title_ru, rss):
    prompt = f"""
    Translate the following Russian news title into natural Japanese for a news site.
    - Title should be concise and catchy.
    - Do not add extra explanations.
    - Translate all the words into officially correct Japanese.
    - If media company name or organization name or person name are included in the title, translate them into officially correct Japanese.
    - Return only the translated title.

    Title: {title_ru}
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
                if isinstance(error, RateLimitError):
                    continue
                
                logger.error(f"Error for model {model}: {e}")
                rss.last_error = f"{error.user_message} while translating title"
                rss.save()
                continue

    return None

def pick_up_news_article_topic(title, topics, rss):
    prompt = f"""
    Classify the following news article title into some of the following topics. 
    - Do not add any extra explanations.
    - Return only the topic names separated by commas.
    
    Title: {title}
    
    Topics: {', '.join([topic.name_en for topic in topics])}
    """
    
    client = Groq(api_key = GROQ_API_KEY)
    models = [GROQ_MODEL_1, GROQ_MODEL_2, GROQ_MODEL_3]

    for model in models:
        try:
            response = client.chat.completions.create(
                model = model,
                messages = [{"role": "system", "content": prompt}],
            )
            suggested_topics = response.choices[0].message.content.split(",")
            matched_topics = []

            for suggested_topic in suggested_topics:
                for topic in topics:
                    if topic.name_en == suggested_topic.strip():
                        matched_topics.append(topic)
            return matched_topics
        except Exception as e:
            error = convert_to_custom_ai_exception(e)
            if isinstance(error, RateLimitError):
                continue
            
            logger.error(f"Error for model {model}: {e}")
            rss.last_error = f"{error.user_message} while picking up topics"
            rss.save()
            continue
    
    return None

def get_news_article_content(rss, url):
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
    try:
        downloaded = requests.get(url, headers = headers)
        downloaded.raise_for_status()
        article_content = trafilatura.extract(downloaded.text)
            
        if article_content is None or len(article_content) == 0:
            return None
            
        cleaned_article_content = clean_article_content(article_content, rss)

        if cleaned_article_content is None or len(cleaned_article_content) == 0:
            return None

        return cleaned_article_content
    except Exception as e:
        logger.error(f'Exception in get_news_article_content: {e}')
        rss.last_error = f"{e} while getting news article content"
        rss.save()
        return None

def delete_old_news_articles():
    for rss in NewsRss.objects.all():
        day = DISPLAY_DAY_LIMIT
        old_news_articles = NewsArticle.objects.filter(rss = rss, created_at__lt = timezone.now() - timedelta(days = day))
        deleted_count = old_news_articles.count()

        try:
            with transaction.atomic():
                for old_news_article in old_news_articles:
                    if old_news_article.image:
                        old_news_article.image.delete()
                
                old_news_articles.delete()
                rss.total_articles = NewsArticle.objects.filter(rss = rss).count()
                rss.save()
        except Exception as e:
            logger.error(f'Error deleting old news articles from {rss.company}: {e}')
            rss.last_error = 'Error deleting old news articles'
            rss.save()
            continue

        logger.info(f"Deleted {deleted_count} old news articles from {rss.company}.")