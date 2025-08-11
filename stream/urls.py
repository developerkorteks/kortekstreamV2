from django.urls import path
from .views import root, home, anime_detail, latest, schedule, search
app_name = 'stream'
urlpatterns = [
        path('', root, name='root'),
        path('detail/', anime_detail, name='anime_detail'),
        path('latest/', latest, name='latest'),
        path('schedule/', schedule, name='schedule'),
        path('search/', search, name='search'),
        path('<str:category>/', home, name='index'),
        ]
