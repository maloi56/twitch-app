import os
import time

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'twitch.settings')

app = Celery('twitch')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task()
def debug_task():
    time.sleep(20)
    print('Hello form debug_task')
