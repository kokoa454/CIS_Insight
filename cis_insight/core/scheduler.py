import logging
import signal
import sys
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from news.batch import (delete_old_news_articles, fetch_telegram_news_articles,
                        fetch_web_news_articles)
from users.batch import (delete_email_change, delete_password_reset,
                         delete_pre_user, expire_email_change,
                         expire_password_reset, expire_pre_user)

logger = logging.getLogger(__name__)

def start():
    def signal_handler(sig, frame):
        scheduler.shutdown(wait = False)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    scheduler = BackgroundScheduler(daemon = True)

    # news
    scheduler.add_job(delete_old_news_articles, 'interval', hours = 1, next_run_time = datetime.now(), coalesce = True)
    scheduler.add_job(fetch_web_news_articles, 'interval', minutes = 15, next_run_time = datetime.now(), coalesce = True)
    scheduler.add_job(fetch_telegram_news_articles, 'interval', minutes = 15, next_run_time = datetime.now(), coalesce = True)

    # users
    scheduler.add_job(expire_email_change, 'interval', minutes = 5, next_run_time = datetime.now(), coalesce = True)
    scheduler.add_job(delete_email_change, 'interval', minutes = 5, next_run_time = datetime.now(), coalesce = True)
    scheduler.add_job(expire_pre_user, 'interval', minutes = 5, next_run_time = datetime.now(), coalesce = True)
    scheduler.add_job(delete_pre_user, 'interval', minutes = 5, next_run_time = datetime.now(), coalesce = True)
    scheduler.add_job(expire_password_reset, 'interval', minutes = 5, next_run_time = datetime.now(), coalesce = True)
    scheduler.add_job(delete_password_reset, 'interval', minutes = 5, next_run_time = datetime.now(), coalesce = True)
    
    scheduler.start()
