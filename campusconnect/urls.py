"""
URL configuration for campusconnect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from chat import views
from django.contrib.auth.models import User

# Import Channels consumers
from chat import consumers

http_urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('chat.urls')),
    path('chatbot/', include('chatbot.urls', namespace='chatbot')),
    path('accounts/', include('django.contrib.auth.urls')),
]

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>.+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/(?P<user_id>\d+)/$', consumers.NotificationConsumer.as_asgi()),
]

urlpatterns = http_urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ASGI application for Channels
# NOTE: This part is for the ASGI server (Daphne/Uvicorn) and is typically in asgi.py
# However, for clarity in demonstrating both URL types in one file, it's shown here.
# In a real project, you would configure this in your asgi.py file.
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack

# application = ProtocolTypeRouter({
#     "http": URLRouter(http_urlpatterns),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(websocket_urlpatterns)
#     ),
# })
