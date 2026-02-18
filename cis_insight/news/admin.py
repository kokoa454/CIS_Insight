from django.contrib import admin
from .models import CisCountry, CisAndNeighborCountry, Topic, NewsRss, NewsArticle

# Register your models here.
admin.site.register(CisCountry)
admin.site.register(CisAndNeighborCountry)
admin.site.register(Topic)
admin.site.register(NewsRss)
admin.site.register(NewsArticle)
