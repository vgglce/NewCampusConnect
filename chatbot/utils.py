import requests
from django.conf import settings

def ask_ollama(prompt):
    try:
        response = requests.post(
            settings.OLLAMA_API_URL,
            json={
                "model": "mistral",
                "prompt": prompt
            }
        )
        return response.json().get("response", "Yanıt alınamadı.")
    except Exception as e:
        return f"Hata oluştu: {e}"
