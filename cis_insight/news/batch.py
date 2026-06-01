from .models import NewsRss, NewsArticle, Topic
import logging
import feedparser
from django.conf import settings
from google import genai
from groq import Groq
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile

import datetime
import time
import requests
import random
import string
from PIL import Image
from io import BytesIO

import sys

from core.exceptions import RateLimitError
from core.settings import MAXIMUM_IMAGE_SIZE_PIXEL

logger = logging.getLogger(__name__)

# Webサイト用
def fetch_web_news_articles():
    processed_urls = set()
    all_topics = list(Topic.objects.all())

    for rss in NewsRss.objects.filter(is_active = True):
        pending_articles = []

        try:
            feed = feedparser.parse(rss.url)
            
            feed_urls = [entry.link for entry in feed.entries if 'link' in entry]
            
            existing_urls = NewsArticle.objects.filter(url__in = feed_urls).values_list('url', flat = True)
            existing_urls = set(existing_urls)

            try:
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

                    if url in processed_urls or url in existing_urls:
                        continue
                    processed_urls.add(url)

                    title_ru = entry.title

                    try:
                        topic = pick_up_news_article_topic(title_ru, all_topics)

                        if topic is None:
                            continue

                        title_ja = translate_title(title_ru)

                        if title_ja is None:
                            continue
                    except RateLimitError:
                        logger.error(f'Rate limit error while translating topics or title')
                        rss.last_error = 'Rate limit error while translating topics or title'
                        rss.save()
                        return
                    except Exception as e:
                        logger.error(f'Error translating topics or title: {e}')
                        rss.last_error = f'Error translating topics or title: {e}'
                        rss.save()
                        continue

                    if 'published_parsed' in entry:
                        published_at = timezone.make_aware(datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed)), datetime.timezone.utc)
                    else:
                        published_at = None
                    
                    if 'enclosures' in entry and len(entry.enclosures) > 0:
                        image_url = entry.enclosures[0].href
                    elif 'media_content' in entry and len(entry.media_content) > 0:
                        image_url = entry.media_content[0]['url']
                    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                        image_url = entry.media_thumbnail[0]['url']
                    else:
                        image_url = None
                    
                    if image_url is not None:
                        try:
                            image = download_image(image_url)
                        except Exception as e:
                            logger.error(f'Error downloading image from {image_url}: {e}')
                            image = None
                    else:
                        image = None
                    
                    country = rss.country

                    is_title_added = True if title_ru is not None else False
                    is_title_translated = True if title_ja is not None else False
                    is_topic_picked = True if topic is not None else False

                    if is_title_added and is_title_translated and is_topic_picked:
                        is_active = True
                    else:
                        is_active = False

                    news_article = NewsArticle(
                        url = url,
                        title_ru = title_ru,
                        title_ja = title_ja,
                        published_at = published_at,
                        country = country,
                        image = image,
                        rss = rss,
                        is_active = is_active,
                        is_title_added = is_title_added,
                        is_title_translated = is_title_translated,
                        is_topic_picked = is_topic_picked,
                    )
                    pending_articles.append((news_article, topic))
            finally:
                if pending_articles:
                    with transaction.atomic():
                        for news_article, topic_list in pending_articles:
                            if not NewsArticle.objects.filter(url = news_article.url).exists():
                                news_article.save()
                                news_article.topic.set(topic_list)
                
                rss.total_articles = NewsArticle.objects.filter(rss = rss).count()
                rss.last_fetched_at = timezone.now()
                rss.save()
            
            time.sleep(2)
        except Exception as e:
            logger.error(f'Error fetching news articles from {rss.url}: {e}')
            rss.last_error = e
            rss.save()

def download_image(image_url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    if image_url is not None and (image_url.startswith('http://') or image_url.startswith('https://')):
        try:
            image_data = requests.get(image_url, timeout = 10, headers = headers)

            if image_data.status_code != 200:
                image = None
            else:
                image_name = ''.join(random.choices(string.ascii_letters + string.digits, k = 128)) + '.png'
                image = enhance_image(BytesIO(image_data.content), image_name)
        except Exception as e:
            logger.error(f'Error enhancing image from {image_url}: {e}')
            image = None
    else:
        image = None
    return image

def enhance_image(image, image_name, size = MAXIMUM_IMAGE_SIZE_PIXEL):
    image = Image.open(image)
    image = image.convert("RGBA")

    w, h = image.size
    target_w, target_h = size

    scale = max(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    image = image.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h
    image = image.crop((left, top, right, bottom))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return InMemoryUploadedFile(buffer, None, image_name, 'image/png', sys.getsizeof(buffer), None)

# Telegram用
def fetch_telegram_news_articles():
    # todo
    pass

# 共通
def translate_title(title_ru):
    prompt = f"""
    Translate the following Russian news title into natural Japanese for a news site.
    - Title should be concise and catchy.
    - Do not add extra explanations.
    - Translate all the words into officially correct Japanese.
    - If media company name or organization name or person name are included in the title, translate them into officially correct Japanese.
    - Return only the translated title.

    Title: {title_ru}
    """

    client = genai.Client(api_key = settings.GEMINI_API_KEY)
    models = [settings.GEMINI_MODEL_1, settings.GEMINI_MODEL_2, settings.GEMINI_MODEL_3]

    for model in models:
        try:
            response = client.models.generate_content(
                model = model,
                contents = prompt,
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e):
                logger.warning(f"Rate limit hit for model {model}.")
                continue
            else:
                logger.error(f'Error translating title from {title_ru}: {e}')
                continue
    raise RateLimitError()

def pick_up_news_article_topic(title, topics):
    prompt = f"""
    Classify the following news article title into some of the following topics. 
    - Do not add any extra explanations.
    - Return only the topic names separated by commas.
    
    Title: {title}
    
    Topics: {', '.join([topic.name_en for topic in topics])}
    """
    
    client = Groq(api_key = settings.GROQ_API_KEY)
    models = [settings.GROQ_MODEL_1, settings.GROQ_MODEL_2]

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
            if "429" in str(e):
                logger.warning(f"Rate limit hit for model {model}.")
                continue
            else:
                logger.error(f'Error picking up news article topic from {title}: {e}')
                continue
    raise RateLimitError()
