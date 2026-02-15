from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

# ダッシュボードページ関連
@login_required
def render_dashboard_page(request):
    user = get_user_model().objects.get(pk=request.user.pk)
    return render(request, 'dashboard.html', {'user': user})