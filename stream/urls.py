from django.urls import path
from .views import root, home, anime_detail, latest, schedule, search, episode_detail
app_name = 'stream'
urlpatterns = [
        path('', root, name='root'),
        path('detail/', anime_detail, name='anime_detail'),
        path('episode/<str:encoded_id>/', episode_detail, name='episode_detail'),
        path('episode/', episode_detail, name='episode_detail_legacy'),  # Keep for backward compatibility
        path('latest/', latest, name='latest'),
        path('schedule/', schedule, name='schedule'),
        path('search/', search, name='search'),
        path('<str:category>/', home, name='index'),
        ]
