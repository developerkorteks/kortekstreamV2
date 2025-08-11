from django.shortcuts import render
from django.core.cache import cache
import requests

BASE_URL = 'http://apigatway.humanmade.my.id:8080'

def home(request, category):
    cache_key = f"home_data_{category}"
    data = cache.get(cache_key)  # cek apakah sudah ada di cache
    if not data:
        try:
            res = requests.get(BASE_URL + '/api/v1/home', params={'category': category}, timeout=5)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            data = {"error": str(e)}
        # Validasi confidence_score
        if data.get("confidence_score", 0) <= 0.5:
            data = {
                "message": "Something went wrong",
                "confidence_score": data.get("confidence_score", 0)
            }
        # Simpan ke cache (misal 60 detik)
        cache.set(cache_key, data, timeout=60)
    context = {
        "datas": data,
        "category": category,
    }
    return render(request, 'stream/index.html', context)

