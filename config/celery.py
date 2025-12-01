# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# read broker/backend from Django settings (optional override here)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from installed apps (looks for tasks.py)
app.autodiscover_tasks()

# Optional: set a nice default
app.conf.task_default_queue = 'default'
