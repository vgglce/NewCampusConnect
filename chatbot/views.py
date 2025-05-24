import requests
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ChatMessage
import logging
import json
from functools import lru_cache
from django.conf import settings
OLLAMA_API_URL = settings.OLLAMA_API_URL


logger = logging.getLogger(__name__)


def get_ollama_response(prompt):
    """Ollama API'ye istek gönder"""
    enhanced_prompt = f"""Sen bir Türkçe asistan olarak görev yapıyorsun. Lütfen aşağıdaki kurallara dikkat ederek yanıt ver:

    1. Düzgün ve akıcı Türkçe kullan
    2. Devrik cümlelerden kaçın, düz cümle yapısı kullan
    3. Günlük konuşma dilini kullan ama resmiyetten de uzak durma
    4. Yanıtların kısa ve öz olsun
    5. Her zaman nazik ve yardımsever ol
    6. Türkçe dilbilgisi kurallarına uygun yaz
    7. Noktalama işaretlerini doğru kullan
    8. Yanıtlarında emoji kullanma
    9. Her yanıtı yeni bir paragrafta başlat
    10. Kullanıcıya "siz" diye hitap et
    11. Yanıtlarınızı 1-2 cümle ile sınırla
    12. Her yanıtınızda bir soru sorarak diyaloğu devam ettir
    13. Yanıtlarınızda gereksiz tekrarlardan kaçının
    14. Kullanıcının sorusunu tam olarak anladığınızdan emin olun
    15. Eğer soruyu anlamadıysanız, açıklama isteyin
    16. Yanıtlarınızda net ve kesin ifadeler kullanın
    17. Kullanıcının seviyesine uygun bir dil kullanın
    18. Her yanıtınızda bir öneri veya tavsiye içerik
    19. Yanıtlarınızda örnekler verin
    20. Kullanıcıyı motive edici bir dil kullanın

    Kullanıcı mesajı: {prompt}"""
    
    payload = {
        "model": "mistral",
        "prompt": enhanced_prompt,
        "stream": False,
        "temperature": 0.5,
        "top_p": 0.8,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=30
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
            logger.error(f"View error: {str(e)}")
            return JsonResponse(
                {'response': "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."},
                status=200
            )

    else:
        history = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:10]
        return render(request, 'chatbot/chat.html', {"messages": reversed(history)})