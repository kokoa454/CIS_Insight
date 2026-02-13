from django.shortcuts import render

# ダッシュボードページ関連
def render_dashboard_page(request):
    return render(request, 'dashboard.html')