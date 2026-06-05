from core.settings import (MAXIMUM_COMPANY_LENGTH, MAXIMUM_COUNTRY_CODE_LENGTH,
                           MAXIMUM_COUNTRY_NAME_LENGTH,
                           MAXIMUM_TOPIC_EMOJI_LENGTH,
                           MAXIMUM_TOPIC_NAME_LENGTH, NEWS_IMAGE_URL)
from django.db import models


# CIS国と周辺国登録用
class CisAndNeighborCountry(models.Model):
    id = models.AutoField(
        primary_key = True,
        verbose_name = 'ID'
    )

    country_code = models.CharField(
        max_length = MAXIMUM_COUNTRY_CODE_LENGTH,
        verbose_name = 'Country Code',
        unique = True
    )

    name = models.CharField(
        max_length = MAXIMUM_COUNTRY_NAME_LENGTH,
        verbose_name = 'Name',
        unique = True
    )

    svg_path = models.TextField(
        verbose_name = 'Path'
    )

    def __str__(self):
        return self.name

# CIS国登録用
class CisCountry(models.Model):
    id = models.AutoField(
        primary_key = True,
        verbose_name = 'ID'
    )

    country_code = models.CharField(
        max_length = MAXIMUM_COUNTRY_CODE_LENGTH,
        verbose_name = 'Country Code',
        unique = True
    )

    name = models.CharField(
        max_length = MAXIMUM_COUNTRY_NAME_LENGTH,
        verbose_name = 'Name',
        unique = True
    )

    svg_path = models.TextField(
        verbose_name = 'Path'
    )

    def __str__(self):
        return self.name

# トピック登録用
class Topic(models.Model):
    id = models.AutoField(
        primary_key = True,
        verbose_name = 'ID'
    )

    name_en = models.CharField(
        max_length = MAXIMUM_TOPIC_NAME_LENGTH,
        verbose_name = 'Name (EN)',
        unique = True
    )

    name_ja = models.CharField(
        max_length = MAXIMUM_TOPIC_NAME_LENGTH,
        verbose_name = 'Name (JA)',
        unique = True
    )

    emoji = models.CharField(
        max_length = MAXIMUM_TOPIC_EMOJI_LENGTH,
        verbose_name = 'Emoji',
        null = True,
        blank = True
    )

    def __str__(self):
        return self.name_ja

# RSS登録用
class NewsRss(models.Model):
    id = models.AutoField(
        primary_key = True,
        verbose_name = 'ID'
    )

    company = models.CharField(
        max_length = MAXIMUM_COMPANY_LENGTH,
        verbose_name = 'Company',
        unique = True
    )

    url = models.URLField(
        verbose_name = 'URL',
        unique = True
    )

    created_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = 'Created At'
    )

    updated_at = models.DateTimeField(
        auto_now = True,
        verbose_name = 'Updated At'
    )

    country = models.ForeignKey(
        CisCountry,
        on_delete = models.PROTECT,
        verbose_name = 'Country'
    )

    is_active = models.BooleanField(
        default = False,
        verbose_name = 'Is Active'
    )

    last_fetched_at = models.DateTimeField(
        verbose_name = 'Last Fetched At',
        null = True,
        blank = True
    )

    total_articles = models.IntegerField(
        default = 0,
        verbose_name = 'Total Articles'
    )

    last_error = models.TextField(
        verbose_name = 'Last Error',
        null = True,
        blank = True
    )

    def __str__(self):
        return self.company

# ニュース記事登録用
class NewsArticle(models.Model):
    id = models.AutoField(
        primary_key = True,
        verbose_name = 'ID'
    )

    title_ru = models.TextField(
        verbose_name = 'Title RU'
    )

    title_ja = models.TextField(
        verbose_name = 'Title JA',
        null = True,
        blank = True
    )

    published_at = models.DateTimeField(
        verbose_name = 'Published At'
    )

    content_ru = models.TextField(
        verbose_name = 'Content RU',
        null = True,
        blank = True
    )

    content_ja = models.TextField(
        verbose_name = 'Content JA',
        null = True,
        blank = True
    )

    url = models.URLField(
        verbose_name = 'URL',
        unique = True
    )

    country = models.ForeignKey(
        CisCountry,
        on_delete = models.PROTECT,
        verbose_name = 'Country'
    )

    topic = models.ManyToManyField(
        Topic,
        verbose_name = 'Topic'
    )

    image = models.ImageField(
        upload_to = NEWS_IMAGE_URL,
        verbose_name = 'Image',
        null = True,
        blank = True
    )

    read_count = models.PositiveIntegerField(
        default = 0,
        verbose_name = 'Read Count'
    )

    rss = models.ForeignKey(
        NewsRss,
        on_delete = models.PROTECT,
        verbose_name = 'RSS',
        null = True,
        blank = True
    )

    created_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = 'Created At'
    )

    updated_at = models.DateTimeField(
        auto_now = True,
        verbose_name = 'Updated At'
    )

    is_active = models.BooleanField(
        default = True,
        verbose_name = 'Is Active'
    )

    is_title_added = models.BooleanField(
        default = False,
        verbose_name = 'Is Title Added'
    )

    is_title_translated = models.BooleanField(
        default = False,
        verbose_name = 'Is Title Translated'
    )

    is_topic_picked = models.BooleanField(
        default = False,
        verbose_name = 'Is Topic Picked'
    )

    is_content_added = models.BooleanField(
        default = False,
        verbose_name = 'Is Content Added'
    )

    is_content_translated = models.BooleanField(
        default = False,
        verbose_name = 'Is Content Translated'
    )

    def __str__(self):
        return self.title_ru

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields = ["-published_at"]),
            models.Index(fields = ["country"]),
            models.Index(fields = ["is_active"]),
            models.Index(fields = ["rss"]),
        ]
