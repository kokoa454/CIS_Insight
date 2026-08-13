from django.db import close_old_connections
import datetime
import json
import logging
import random
import string
import time
from datetime import timedelta
from io import BytesIO

import feedparser
import newspaper
import trafilatura
from core.exceptions import (RateLimitError, ServerError,
                             convert_to_custom_ai_exception)
from core.settings import (ALLOWED_IMAGE_SIZE, ALLOWED_IMAGE_TYPE, CHUNK_SIZE,
                           DEFAULT_HEADERS, DISPLAY_DAY_LIMIT,
                           GEMINI_API_KEY_1, GEMINI_API_KEY_2,
                           GEMINI_API_KEY_3, GEMINI_API_KEY_4,
                           GEMINI_API_KEY_5, GEMINI_MODEL_1, GEMINI_MODEL_2,
                           GEMINI_MODEL_3, GEMINI_MODEL_4, GEMINI_MODEL_5,
                           GEMMA_MODEL_1, GEMMA_MODEL_2, GROQ_API_KEY,
                           GROQ_MODEL_1, GROQ_MODEL_2, GROQ_MODEL_3,
                           IMPERSONATE_TARGET, MAXIMUM_IMAGE_SIZE_PIXEL)
from core.utils import is_safe_url
from curl_cffi import requests
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from google import genai
from groq import Groq
from PIL import Image

from .models import NewsArticle, NewsRss, Topic

logger = logging.getLogger(__name__)

# API制限時間の管理用
COOLDOWN_REGISTRY = {}

def is_cooldown(target, api_key = None):
    registry_key = f"{target}_{api_key}" if api_key else target

    now = timezone.now()
    if registry_key in COOLDOWN_REGISTRY:
        if now < COOLDOWN_REGISTRY[registry_key]:
            return True
        else:
            del COOLDOWN_REGISTRY[registry_key]  
    return False

def set_cooldown(target, hours = 2, api_key = None):
    registry_key = f"{target}_{api_key}" if api_key else target
    COOLDOWN_REGISTRY[registry_key] = timezone.now() + timedelta(hours = hours)

# Webサイト用
def fetch_web_news_articles():
    close_old_connections()

    all_topics = list(Topic.objects.all())

    active_rss_list = NewsRss.objects.filter(is_active=True).order_by(F('last_fetched_at').asc(nulls_first=True))

    for rss in active_rss_list:
        try:
            valid_entries = fetch_and_filter_feed_entries(rss)

            if not valid_entries:
                continue

            chunk_size = 10
            for i in range(0, len(valid_entries), chunk_size):
                chunk_entries = valid_entries[i:i + chunk_size]

                chunk_items = initialize_chunk_articles(chunk_entries, rss)
                if not chunk_items:
                    continue

                translate_and_classify_chunk(chunk_items, rss, all_topics)
                extract_and_clean_contents_chunk(chunk_items, rss)
                translate_and_save_articles_chunk(chunk_items, rss)

            rss.total_articles = NewsArticle.objects.filter(rss=rss).count()
            rss.last_fetched_at = timezone.now()
            rss.save()

        except Exception as e:
            logger.error(f'Error processing RSS {rss.url}: {e}')
        finally:
            close_old_connections()

def fetch_and_filter_feed_entries(rss):
    processed_urls = set()
    valid_entries = []

    try:
        downloaded = requests.get(rss.url, headers=DEFAULT_HEADERS, impersonate=IMPERSONATE_TARGET, timeout=30)
        downloaded.raise_for_status()
        feed = feedparser.parse(downloaded.content)

    except Exception as e:
        logger.error(f'Error fetching RSS feed from {rss.url}: {e}')
        rss.last_error = str(e)
        rss.last_error_at = timezone.now()
        rss.save()
        return []

    existing_articles = {
        a.url: a
        for a in NewsArticle.objects.filter(
            url__in=[entry.link for entry in feed.entries if 'link' in entry]
        ).prefetch_related('topic')
    }
    completed_urls = {url for url, a in existing_articles.items() if a.is_active}

    for idx, entry in enumerate(feed.entries):
        if idx % 5 == 0:
            try:
                rss.refresh_from_db()
                if not rss.is_active:
                    logger.info(f"RSS {rss.url} became inactive during processing. Aborting.")
                    return []
            except ObjectDoesNotExist:
                return []

        if 'link' not in entry or 'title' not in entry:
            continue

        url = entry.link

        if url in processed_urls or url in completed_urls:
            continue

        if not is_safe_url(url):
            logger.warning(f'SSRF prevention triggered: Blocked URL pointing to internal IP {url}')
            continue

        processed_urls.add(url)
        
        valid_entries.append({
            "url": url,
            "entry": entry,
            "existing_article": existing_articles.get(url)
        })

    return valid_entries

def initialize_chunk_articles(chunk_entries, rss):
    chunk_items = []
    
    for item in chunk_entries:
        url = item["url"]
        entry = item["entry"]
        existing_article = item["existing_article"]
        title_ru = entry.title

        has_topic = existing_article and existing_article.is_topic_picked
        has_translation = existing_article and existing_article.is_title_translated
        has_content = existing_article and existing_article.is_content_added

        if 'published_parsed' in entry:
            published_at = timezone.make_aware(
                datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed)),
                datetime.timezone.utc
            )
        else:
            published_at = None

        image = None
        if not (existing_article and existing_article.image):
            image_url = None
            if 'enclosures' in entry and len(entry.enclosures) > 0:
                image_url = entry.enclosures[0].href
            elif 'media_content' in entry and len(entry.media_content) > 0:
                image_url = entry.media_content[0]['url']
            elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                image_url = entry.media_thumbnail[0]['url']

            if image_url:
                if not is_safe_url(image_url):
                    logger.warning(f'SSRF prevention triggered: Blocked URL pointing to internal IP {image_url}')
                else:
                    try:
                        image = download_image_from_rss(image_url)
                    except Exception:
                        image = None
            else:
                try:
                    image = download_image_from_article(url)
                except Exception:
                    image = None

        chunk_items.append({
            "existing_article": existing_article,
            "url": url,
            "title_ru": title_ru,
            "published_at": published_at,
            "image": image,
            "has_topic": has_topic,
            "has_translation": has_translation,
            "has_content": has_content,
            "raw_content_ru": None,
            "content_ru": existing_article.content_ru if has_content else None,
            "title_ja": existing_article.title_ja if has_translation else None,
            "topic": list(existing_article.topic.all()) if has_topic else []
        })
        
    return chunk_items

def translate_and_classify_chunk(chunk_items, rss, all_topics):
    titles_to_translate = [item["title_ru"] for item in chunk_items if not item["has_translation"]]
    titles_to_classify = [item["title_ru"] for item in chunk_items if not item["has_topic"]]

    if titles_to_translate or titles_to_classify:
        time.sleep(random.uniform(2.0, 3.5))

    if titles_to_translate:
        try:
            translated_list = translate_titles_batch(titles_to_translate, rss)
            translated_map = {orig: trans for orig, trans in zip(titles_to_translate, translated_list) if trans}

            for item in chunk_items:
                if not item["has_translation"] and item["title_ru"] in translated_map:
                    item["title_ja"] = translated_map[item["title_ru"]]

        except Exception as e:
            logger.error(f"Batch title translation crashed: {e}")

    if titles_to_classify:
        try:
            time.sleep(0.5)
            topic_map = pick_up_news_articles_topics_batch(titles_to_classify, all_topics, rss)

            for item in chunk_items:
                if not item["has_topic"] and item["title_ru"] in topic_map:
                    item["topic"] = topic_map[item["title_ru"]]

        except Exception as e:
            logger.error(f"Batch topic classification crashed: {e}")

def extract_and_clean_contents_chunk(chunk_items, rss):
    contents_to_clean = {}

    for item in chunk_items:
        if item["has_content"]:
            continue

        time.sleep(1)

        try:
            doc_downloaded = requests.get(item["url"], headers=DEFAULT_HEADERS, impersonate=IMPERSONATE_TARGET, timeout=30)
            doc_downloaded.raise_for_status()
            extracted_text = trafilatura.extract(doc_downloaded.text)

            if extracted_text:
                contents_to_clean[item["url"]] = extracted_text
        except Exception as e:
            logger.error(f'Exception while extracting raw content for {item["url"]}: {e}')

    if contents_to_clean:
        try:
            time.sleep(1.5)
            cleaned_contents_map = clean_articles_contents_batch(contents_to_clean, rss)

            for item in chunk_items:
                if not item["has_content"] and item["url"] in cleaned_contents_map:
                    item["content_ru"] = cleaned_contents_map[item["url"]]
        except Exception as e:
            logger.error(f"Batch content cleaning crashed: {e}")

def translate_and_save_articles_chunk(chunk_items, rss):
    contents_to_translate = []

    for item in chunk_items:
        ru_text = item["content_ru"]
        has_trans_ja = item["existing_article"] and getattr(item["existing_article"], "is_content_translated", False)

        if ru_text and ru_text.strip() and not has_trans_ja:
            contents_to_translate.append(ru_text)

    translated_contents_map = {}

    if contents_to_translate:
        try:
            time.sleep(1.5)
            content_chunk_size = 3

            for sub_i in range(0, len(contents_to_translate), content_chunk_size):
                sub_chunk = contents_to_translate[sub_i:sub_i + content_chunk_size]
                translated_content_list = translate_content_batch(sub_chunk, rss)

                if not translated_content_list:
                    logger.warning(f"Sub-chunk translation skipped due to model output error. Chunk size: {len(sub_chunk)}")
                    continue

                for orig_ru, trans_ja in zip(sub_chunk, translated_content_list):
                    if trans_ja:
                        for item in chunk_items:
                            item_ru = item["content_ru"]

                            if item_ru and item_ru.strip() == orig_ru.strip():
                                translated_contents_map[item["url"]] = trans_ja
                                break
                time.sleep(1.0)

        except Exception as e:
            logger.error(f"Batch content translation crashed: {e}")

    articles_to_create = []
    articles_to_update = []
    m2m_updates = []

    for item in chunk_items:
        url = item["url"]
        existing_article = item["existing_article"]
        title_ru = item["title_ru"]
        title_ja = existing_article.title_ja if item["has_translation"] else item.get("title_ja")
        topic = item["topic"]
        topic_changed = not item["has_topic"]
        content_ru = item["content_ru"]
        is_content_added = bool(content_ru and str(content_ru).strip())

        has_trans_ja = existing_article and getattr(existing_article, "is_content_translated", False)
        content_ja = existing_article.content_ja if has_trans_ja else translated_contents_map.get(url)
        is_content_translated = bool(content_ja and str(content_ja).strip())

        if title_ja is None and not existing_article:
            continue

        if not item["has_topic"] and not topic:
            continue

        is_title_added = bool(title_ru and str(title_ru).strip())
        is_title_translated = bool(title_ja and str(title_ja).strip())
        is_topic_picked = bool(topic)
        is_active = is_title_added and is_title_translated and is_topic_picked

        if existing_article:
            if title_ru: existing_article.title_ru = title_ru
            if title_ja: existing_article.title_ja = title_ja
            existing_article.published_at = item["published_at"]
            existing_article.country = rss.country
            existing_article.is_active = is_active
            existing_article.is_title_added = is_title_added
            existing_article.is_title_translated = is_title_translated
            existing_article.is_topic_picked = is_topic_picked

            if not existing_article.is_content_added and is_content_added:
                existing_article.content_ru = content_ru
                existing_article.is_content_added = True

            if not getattr(existing_article, 'is_content_translated', False) and is_content_translated:
                existing_article.content_ja = content_ja
                existing_article.is_content_translated = True

            if item["image"]:
                existing_article.image = item["image"]

            articles_to_update.append(existing_article)

            if topic_changed:
                m2m_updates.append((existing_article, topic))
        else:
            new_article = NewsArticle(
                url=url,
                title_ru=title_ru,
                title_ja=title_ja,
                published_at=item["published_at"],
                country=rss.country,
                image=item["image"],
                rss=rss,
                content_ru=content_ru,
                content_ja=content_ja,
                is_active=is_active,
                is_title_added=is_title_added,
                is_title_translated=is_title_translated,
                is_topic_picked=is_topic_picked,
                is_content_added=is_content_added,
                is_content_translated=is_content_translated,
            )
            articles_to_create.append(new_article)
            m2m_updates.append((new_article, topic))

    if articles_to_create or articles_to_update:
        try:
            with transaction.atomic():
                if articles_to_create:
                    created_articles = NewsArticle.objects.bulk_create(
                        articles_to_create, 
                        ignore_conflicts=True
                    )

                    for idx, (article_obj, topics) in enumerate(m2m_updates):
                        if article_obj.pk is None: 
                            matched = next((a for a in created_articles if a.url == article_obj.url and a.pk is not None), None)
                            if matched:
                                m2m_updates[idx] = (matched, topics)
                            else:
                                m2m_updates[idx] = (None, [])

                if articles_to_update:
                    fields_to_update = [
                        'title_ru', 'title_ja', 'published_at', 'country', 'image',
                        'is_active', 'is_title_added', 'is_title_translated', 'is_topic_picked',
                        'content_ru', 'is_content_added', 'content_ja', 'is_content_translated'
                    ]
                    NewsArticle.objects.bulk_update(articles_to_update, fields=fields_to_update)

                for article_obj, topics in m2m_updates:
                    if article_obj and article_obj.pk is not None:
                        article_obj.topic.set(topics)

                rss.total_articles = NewsArticle.objects.filter(rss = rss).count()
                rss.last_fetched_at = timezone.now()
                rss.save(update_fields = ['total_articles', 'last_fetched_at'])

            logger.info(f"Successfully batch saved {len(articles_to_create)} created and {len(articles_to_update)} updated articles.")

        except Exception as e:
            logger.error(f'Failed to commit batch save for chunk: {e}')

            rss.total_articles = NewsArticle.objects.filter(rss = rss).count()
            rss.last_error = str(e)
            rss.last_error_at = timezone.now()
            rss.save()

def download_image_from_rss(image_url):
    if not (image_url is not None and (image_url.startswith('http://') or image_url.startswith('https://'))):
        logger.warning(f'Invalid image URL: {image_url}')

        return None

    image_data = None

    try:
        image_data = requests.get(image_url, headers = DEFAULT_HEADERS, impersonate = IMPERSONATE_TARGET, stream = True, timeout = 30)
        image_data.raise_for_status()

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

        image_name = ''.join(random.choices(string.ascii_letters + string.digits, k = 64)) + '.webp'
        image = enhance_image(buffer, image_name)

        return image
    except Exception as e:
        logger.error(f'Error enhancing image from {image_url}: {e}')
        return None
    finally:
        if image_data is not None:
            image_data.close()

def download_image_from_article(url):
    if not (url is not None and (url.startswith('http://') or url.startswith('https://'))):
        logger.warning(f'Invalid article URL: {url}')
        return None

    image_data = None

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

        image_data = requests.get(image_url, headers = DEFAULT_HEADERS, impersonate = IMPERSONATE_TARGET, stream = True, timeout = 30)
        image_data.raise_for_status()

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

        image_name = ''.join(random.choices(string.ascii_letters + string.digits, k = 64)) + '.webp'
        image = enhance_image(buffer, image_name)

        return image
    except Exception as e:
        logger.warning(f'Error downloading image from article {url}: {e}')
        return None
    finally:
        if image_data is not None:
            image_data.close()

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
    img.save(buffer, format="WEBP")
    buffer.seek(0)

    size_bytes = buffer.getbuffer().nbytes

    return InMemoryUploadedFile(buffer, None, image_name, 'image/webp', size_bytes, None)


def fetch_telegram_news_articles():
    #TODO テレグラム用の取得を実装
    pass

# --- 記事内容翻訳一括バッチ処理 (Gemini / Gemma) ---
def translate_content_batch(content_ru_list, rss):
    if not content_ru_list:
        return []

    prompt = f"""
    Translate the following Russian news content into natural Japanese for a news site.
    - The input is a JSON array containing {len(content_ru_list)} items.
    - The output MUST be a JSON array containing EXACTLY {len(content_ru_list)} items, in the exact same order.
    - For each item in the provided JSON array, translate the ENTIRE text completely without omitting any parts or summarizing.
    - Translate all the words into officially correct Japanese (である調).
    - If media company name, organization name, person name, or place name are included, translate them into officially correct Japanese.
    - Separate each paragraph with a double newline (\\n\\n).
    - Return ONLY a valid JSON array of strings. Do not include markdown codeblocks, do not add extra text, descriptions, or notes.

    Content:
    {json.dumps(content_ru_list, ensure_ascii=False)}
    """

    api_keys = [GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3, GEMINI_API_KEY_4, GEMINI_API_KEY_5]
    gemini_models = [GEMINI_MODEL_1, GEMINI_MODEL_2, GEMINI_MODEL_3, GEMINI_MODEL_4, GEMINI_MODEL_5]
    gemma_models = [GEMMA_MODEL_1, GEMMA_MODEL_2]
    all_models = gemini_models + gemma_models

    for api_key in api_keys:
        if not api_key or is_cooldown(api_key):
            continue

        try:
            client = genai.Client(api_key=api_key)
            for model in all_models:
                if not model or is_cooldown(model, api_key):
                    continue

                try:
                    response = client.models.generate_content(model=model, contents=prompt)
                    res_text = response.text.strip()

                    if res_text.startswith("```"):
                        res_text = res_text.split("```")[1]

                        if res_text.startswith("json"):
                            res_text = res_text[4:]

                    try:
                        translated_array = json.loads(res_text.strip())

                        if isinstance(translated_array, list) and len(translated_array) == len(content_ru_list):
                            return translated_array
                        else:
                            got_type = type(translated_array).__name__
                            got_len = len(translated_array) if isinstance(translated_array, list) else 'N/A'
                            logger.warning(f"Model {model} returned unexpected format: type={got_type}, len={got_len}, expected_len={len(content_ru_list)}")

                    except json.JSONDecodeError as je:
                        logger.error(f"JSON decode failed for model {model}. Error: {je}")
                        continue

                except Exception as e:
                    error = convert_to_custom_ai_exception(e)

                    if isinstance(error, RateLimitError):
                        logger.warning(f"Rate limit hit. Cooldown activated. Error: {e}")
                        set_cooldown(api_key, hours=2)
                        break

                    if isinstance(error, ServerError):
                        logger.warning(f"Server error hit for model {model}. Cooldown activated. Error: {e}")
                        set_cooldown(model, hours=1, api_key=api_key)
                        continue

                    logger.error(f"Translation model {model} failed: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed initialization with Gemini API Key: {e}")
            continue

    return [None] * len(content_ru_list)

# --- 記事タイトル翻訳一括バッチ処理 (Gemini / Gemma) ---
def translate_titles_batch(titles_ru_list, rss):
    if not titles_ru_list:
        return []

    prompt = f"""
    Translate the following Russian news titles into natural Japanese for a news site.
    - Titles should be concise and catchy.
    - The input is a JSON array containing {len(titles_ru_list)} items.
    - The output MUST be a JSON array containing EXACTLY {len(titles_ru_list)} items, in the exact same order.
    - Translate all words, media company names, organizations, or person names into officially correct Japanese.
    - Return ONLY a valid JSON array of strings containing the translations in the exact same order.
    - Do not markdown codeblocks, do not add extra text, descriptions or notes.

    Titles:
    {json.dumps(titles_ru_list, ensure_ascii=False)}
    """

    api_keys = [GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3, GEMINI_API_KEY_4, GEMINI_API_KEY_5]
    gemini_models = [GEMINI_MODEL_1, GEMINI_MODEL_2, GEMINI_MODEL_3, GEMINI_MODEL_4, GEMINI_MODEL_5]
    gemma_models = [GEMMA_MODEL_1, GEMMA_MODEL_2]
    all_models = gemini_models + gemma_models

    for api_key in api_keys:
        if not api_key:
            continue
        
        if is_cooldown(api_key):
            continue

        try:
            client = genai.Client(api_key = api_key)
            for model in all_models:
                if not model:
                    continue

                if is_cooldown(model, api_key):
                    continue

                try:
                    response = client.models.generate_content(model=model, contents=prompt)
                    res_text = response.text.strip()

                    if res_text.startswith("```"):
                        res_text = res_text.split("```")[1]
                        if res_text.startswith("json"):
                            res_text = res_text[4:]

                    translated_array = json.loads(res_text.strip())

                    if isinstance(translated_array, list) and len(translated_array) == len(titles_ru_list):
                        return translated_array
                except Exception as e:
                    error = convert_to_custom_ai_exception(e)
                    
                    if isinstance(error, RateLimitError):
                        logger.warning(f"Rate limit hit for key. Cooldown activated. Error: {e}")
                        set_cooldown(api_key, hours = 2)
                        break
                        
                    if isinstance(error, ServerError):
                        logger.warning(f"Server error hit for model {model}. Cooldown activated. Error: {e}")
                        set_cooldown(model, hours = 1, api_key = api_key)
                        continue
                        
                    logger.error(f"Translation model {model} failed: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed initialization or execution with Gemini API Key: {e}")
            continue

    return [None] * len(titles_ru_list)

# --- トピック選定一括バッチ処理 (Groq) ---
def pick_up_news_articles_topics_batch(titles_list, topics, rss):
    if not titles_list:
        return {}

    topics_dict = {topic.name_en: topic for topic in topics}
    prompt = f"""
    Classify the following news article titles into some of the given topics.
    - Return ONLY a valid JSON object where the key is the exact original title, and the value is a list of matching topic strings from the permitted topics list.
    - The input is a JSON array containing {len(titles_list)} items.
    - The output MUST be a JSON object containing EXACTLY {len(titles_list)} keys, in the exact same order.
    - Do not include any extra descriptions, markdown, notes or explanations.

    Permitted Topics: {', '.join([topic.name_en for topic in topics])}

    Titles to classify:
    {json.dumps(titles_list, ensure_ascii=False)}
    """

    client = Groq(api_key = GROQ_API_KEY)
    models = [GROQ_MODEL_1, GROQ_MODEL_2, GROQ_MODEL_3]
    matched_topics_map = {}

    for model in models:
        if not model:
            continue
        try:
            response = client.chat.completions.create(
                model = model,
                messages = [{"role": "system", "content": prompt}],
                response_format = {"type": "json_object"}
            )
            raw_content = response.choices[0].message.content.strip()
            classification_results = json.loads(raw_content)

            for orig_title, suggested_topics in classification_results.items():
                if isinstance(suggested_topics, list):
                    obj_list = []
                    for t_name in suggested_topics:
                        cleaned_name = t_name.strip()
                        if cleaned_name in topics_dict:
                            obj_list.append(topics_dict[cleaned_name])
                    matched_topics_map[orig_title] = obj_list
            
            return matched_topics_map
        except Exception as e:
            error = convert_to_custom_ai_exception(e)
            if isinstance(error, RateLimitError) or isinstance(error, ServerError):
                continue
            logger.error(f"Error for Groq model {model}: {e}")
            continue

    return {}

# 本文クレンジング一括バッチ処理 (Gemini / Gemma)
def clean_articles_contents_batch(contents_dict, rss):
    if not contents_dict:
        return {}

    prompt = f"""
    Clean the following Russian news contents.
    - For each item in the provided JSON object, extract ONLY the core narrative text.
    - The input is a JSON object containing {len(contents_dict)} items.
    - The output MUST be a JSON object containing EXACTLY {len(contents_dict)} keys, in the exact same order.
    - Remove the dateline (e.g., "CITY, Date - Agency Name").
    - Remove all noise: ads, social media links, navigation menu, phone numbers, emails, and copyright notices.
    - Remove repetitive titles or image captions.
    - Separate each paragraph with a double newline (\\n\\n).
    - Return ONLY a valid JSON object where the key is the exact same URL identifier and the value is the cleaned plain text string.
    - Do not markdown codeblocks, do not add extra text, descriptions or notes.

    Contents to clean:
    {json.dumps(contents_dict, ensure_ascii=False)}
    """

    api_keys = [GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3, GEMINI_API_KEY_4, GEMINI_API_KEY_5]
    gemini_models = [GEMINI_MODEL_1, GEMINI_MODEL_2, GEMINI_MODEL_3, GEMINI_MODEL_4, GEMINI_MODEL_5]
    gemma_models = [GEMMA_MODEL_1, GEMMA_MODEL_2]
    all_models = gemini_models + gemma_models

    for api_key in api_keys:
        if not api_key:
            continue

        if is_cooldown(api_key):
            continue

        try:
            client = genai.Client(api_key=api_key)

            for model in all_models:
                if not model:
                    continue

                if is_cooldown(model, api_key):
                    continue

                try:
                    response = client.models.generate_content(model=model, contents=prompt)
                    res_text = response.text.strip()

                    if res_text.startswith("```"):
                        res_text = res_text.split("```")[1]
                        if res_text.startswith("json"):
                            res_text = res_text[4:]

                    cleaned_map = json.loads(res_text.strip())

                    if isinstance(cleaned_map, dict):
                        return cleaned_map
                except Exception as e:
                    error = convert_to_custom_ai_exception(e)

                    if isinstance(error, RateLimitError):
                        logger.warning(f"Rate limit hit for key during cleaning. Cooldown activated. Error: {e}")
                        set_cooldown(api_key, hours = 2)
                        break
                        
                    if isinstance(error, ServerError):
                        logger.warning(f"Server error hit for model {model} during cleaning. Cooldown activated. Error: {e}")
                        set_cooldown(model, hours = 1, api_key = api_key)
                        continue

                    logger.error(f"Content cleaning model {model} failed: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed initialization or execution with Gemini API Key for cleaning: {e}")
            continue

    return {}

# 不要な記事を削除
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
            rss.last_error_at = timezone.now()
            rss.save()
            continue

        logger.info(f"Deleted {deleted_count} old news articles from {rss.company}.")
