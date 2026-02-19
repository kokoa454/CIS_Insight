from django.db import models
from core.settings import (MAXIMUM_COMPANY_LENGTH, MAXIMUM_COUNTRY_CODE_LENGTH, MAXIMUM_COUNTRY_NAME_LENGTH, MAXIMUM_TOPIC_NAME_LENGTH, MAXIMUM_TOPIC_EMOJI_LENGTH, NEWS_IMAGE_URL)

# CIS国と周辺国登録用
class CisAndNeighborCountryManager(models.Manager):
    def create_cis_and_neighbor_country(self, country_code, name, svg_path, **extra_fields):
        cis_country_and_neighbor = self.model(
            country_code = country_code,
            name = name,
            svg_path = svg_path,
            **extra_fields
        )
        cis_country_and_neighbor.save(using=self._db)
        return cis_country_and_neighbor

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

    objects = CisAndNeighborCountryManager()

    def __str__(self):
        return self.name

# CIS国登録用
class CisCountryManager(models.Manager):
    def create_cis_country(self, country_code, name, svg_path, **extra_fields):
        cis_country = self.model(
            country_code = country_code,
            name = name,
            svg_path = svg_path,
            **extra_fields
        )
        cis_country.save(using=self._db)
        return cis_country

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

    objects = CisCountryManager()

    def __str__(self):
        return self.name

# トピック登録用
class TopicManager(models.Manager):
    def create_topic(self, name_en, name_ja, emoji, **extra_fields):
        topic = self.model(
            name_en = name_en,
            name_ja = name_ja,
            emoji = emoji,
            **extra_fields
        )
        topic.save(using=self._db)
        return topic

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

    objects = TopicManager()

    def __str__(self):
        return self.name_ja

# RSS登録用
class NewsRssManager(models.Manager):
    def create_news_rss(self, company, url, country, is_active, **extra_fields):
        news_rss = self.model(
            company = company,
            url = url,
            country = country,
            is_active = is_active,
            **extra_fields
        )
        news_rss.save(using=self._db)
        return news_rss

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

    objects = NewsRssManager()

    def __str__(self):
        return self.company

# ニュース記事登録用
class NewsArticleManager(models.Manager):
    def create_news_article(self, title_ru, title_ja, summary_ru, summary_ja, published_at, url, country, topic, image, rss, **extra_fields):
        news_article = self.model(
            title_ru = title_ru,
            title_ja = title_ja,
            summary_ru = summary_ru,
            summary_ja = summary_ja,
            published_at = published_at,
            url = url,
            country = country,
            image = image,
            rss = rss,
            **extra_fields
        )

        news_article.save(using=self._db)

        if topic:
            news_article.topic.set(topic)

        return news_article

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

    summary_ru = models.TextField(
        verbose_name = 'Summary RU',
    )

    summary_ja = models.TextField(
        verbose_name = 'Summary JA',
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

    is_title_translated = models.BooleanField(
        default = False,
        verbose_name = 'Is Title Translated'
    )

    is_summary_translated = models.BooleanField(
        default = False,
        verbose_name = 'Is Summary Translated'
    )

    is_content_added = models.BooleanField(
        default = False,
        verbose_name = 'Is Content Added'
    )

    is_content_translated = models.BooleanField(
        default = False,
        verbose_name = 'Is Content Translated'
    )

    objects = NewsArticleManager()

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
