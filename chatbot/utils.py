import requests
from django.conf import settings
import json

def ask_ollama(prompt):
    try:
        response = requests.post(
            settings.OLLAMA_API_URL,
            json={
                "model": "mistral",
                "prompt": prompt
            },
            timeout=90,
            stream=True
        )
        response.raise_for_status()

        full_response = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8'))
                if "response" in data:
                    full_response += data["response"]

        return full_response or "Yanıt alınamadı."
    except requests.exceptions.Timeout:
        return "Hata: İstek zaman aşımına uğradı."
    except requests.exceptions.HTTPError as err:
        return f"HTTP Hatası: {err}"
    except requests.exceptions.ConnectionError as err:
        return f"Bağlantı Hatası: {err}"
    except Exception as e:
        return f"Genel Hata: {e}"
