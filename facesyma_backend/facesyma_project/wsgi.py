"""facesyma_project/wsgi.py"""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facesyma_project.settings')
application = get_wsgi_application()

# Start background scheduler for gamification tasks
try:
    from admin_api.scheduler import start_scheduler
    start_scheduler()
except Exception as e:
    import logging
    logging.error(f"Failed to start scheduler: {e}")
