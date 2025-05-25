import requests
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ChatMessage
import logging
import json
from functools import lru_cache
from django.conf import settings
import traceback

OLLAMA_API_URL = settings.OLLAMA_API_URL


logger = logging.getLogger(__name__)


def get_ollama_response(prompt):
    """Ollama API'ye istek gönder"""
    enhanced_prompt = f"""Sen Türkçe bilen yardımsever bir asistansın. Sorulara nazik ve net yanıtlar ver. 
    Cevapların sade, açık ve kibar olsun.
    Kullanıcı mesajı: {prompt}"""

    payload = {
        "model": "mistral",
        "prompt": enhanced_prompt,
        "stream": False,
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 500,
    }

    try:
        response = requests.post(
            settings.OLLAMA_API_URL,  # 👈 Doğru adres burası
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=90
        )

        if response.status_code == 200:
            response_data = response.json()
            return response_data.get("response", "")
        else:
            logger.error(f"Ollama API returned status code: {response.status_code}")
            return "Üzgünüm, şu anda yanıt veremiyorum. Lütfen daha sonra tekrar deneyin."

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."


@login_required
def chat_view(request):
    if request.method == 'POST':
        try:
            user_message = request.POST.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({'response': "Mesaj alınamadı. Ne sormak istersiniz?"})

            # Kullanıcının mesajını kaydet
            ChatMessage.objects.create(user=request.user, role='user', message=user_message)

            # Ollama'ya istek gönder
            bot_reply = get_ollama_response(user_message)
            
            # Bot cevabını kaydet
            ChatMessage.objects.create(user=request.user, role='bot', message=bot_reply)

            return JsonResponse({'response': bot_reply})

        except Exception as e:
            logger.error("Gelen hata:\n" + traceback.format_exc())
            return JsonResponse(
                {'response': "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."},
                status=200
            )

    else:
        history = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:10]
        return render(request, 'chatbot/chat.html', {"messages": reversed(history)})