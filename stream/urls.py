from django.urls import path
from .views import home
app_name = 'stream'
urlpatterns = [
        path('<str:category>/', home, name='index' )
        ]
