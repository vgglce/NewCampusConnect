import os
from celery import Celery

# Django ayarlarını varsayılan olarak yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campusconnect.settings')

# Celery uygulamasını oluştur (broker settings.py'den alınacak)
app = Celery('campusconnect')

# Ayarları Django settings üzerinden yükle
# 'CELERY_' prefix'i olan tüm ayarları tanır
app.config_from_object('django.conf:settings', namespace='CELERY')

# Eğer settings.py'de yoksa varsayılan Redis broker'ı kullan
app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')

# Django app’lerindeki tasks.py dosyalarını otomatik tanır
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
