from django.urls import path
from .views import root, home, anime_detail, latest, schedule, search, episode_detail, api_health_check, reset_circuit_breaker
app_name = 'stream'
urlpatterns = [
        path('', root, name='root'),
        path('detail/', anime_detail, name='anime_detail'),
        path('episode/<str:encoded_id>/', episode_detail, name='episode_detail'),
        path('episode/', episode_detail, name='episode_detail_legacy'),  # Keep for backward compatibility
        path('latest/', latest, name='latest'),
        path('schedule/', schedule, name='schedule'),
        path('search/', search, name='search'),
        path('api/health/', api_health_check, name='api_health_check'),
        path('api/reset-circuit-breaker/', reset_circuit_breaker, name='reset_circuit_breaker'),
        path('<str:category>/', home, name='index'),
        ]
