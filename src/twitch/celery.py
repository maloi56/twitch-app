import os
import time

from celery import Celery
# from websockets.chat import tasks

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'twitch.settings')

app = Celery('twitch')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task()
def debug_task():
    time.sleep(20)
    print('Hello form debug_task')