from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from news.models import CisAndNeighborCountry, CisCountry, Topic

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
    return render(request, 'rss_settings.html')

@login_required
def rss_settings(request):
    pass