from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import signal
import sys
import logging

from news.batch import fetch_news_articles
from users.batch import expire_email_change, delete_email_change, expire_pre_user, delete_pre_user

logger = logging.getLogger(__name__)

def start():
    def signal_handler(sig, frame):
        scheduler.shutdown(wait = False)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    scheduler = BackgroundScheduler(daemon = True)

    # news
    scheduler.add_job(fetch_news_articles, 'interval', minutes = 1, next_run_time = datetime.now(), coalesce = True)

    # users
    scheduler.add_job(expire_email_change, 'interval', minutes = 1, next_run_time = datetime.now(), coalesce = True)
    scheduler.add_job(delete_email_change, 'interval', minutes = 1, next_run_time = datetime.now(), coalesce = True)
    scheduler.add_job(expire_pre_user, 'interval', minutes = 1, next_run_time = datetime.now(), coalesce = True)
    scheduler.add_job(delete_pre_user, 'interval', minutes = 1, next_run_time = datetime.now(), coalesce = True)
    
    scheduler.start()
