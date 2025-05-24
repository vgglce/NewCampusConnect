import requests
from django.conf import settings

def ask_ollama(prompt):
    try:
        response = requests.post(
            settings.OLLAMA_API_URL,
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False  # <<< BU SATIR ÖNEMLİ
            },
            timeout=60  # Timeout'u biraz artırdık
        )
        response.raise_for_status()
        data = response.json()
        if "response" in data:
            return data["response"]
        else:
            return f"Beklenmeyen yanıt: {data}"
    except requests.exceptions.Timeout:
        return "Hata: İstek zaman aşımına uğradı."
    except requests.exceptions.HTTPError as err:
        return f"HTTP Hatası: {err}"
    except requests.exceptions.ConnectionError as err:
        return f"Bağlantı Hatası: {err}"
    except Exception as e:
        return f"Genel Hata: {e}"
