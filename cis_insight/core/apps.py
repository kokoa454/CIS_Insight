import sys
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        args = sys.argv
        skip_commands = [
            'collectstatic', 
            'migrate', 
            'makemigrations', 
            'test', 
            'seed_master', 
            'check'
        ]

        if any(cmd in args for cmd in skip_commands):
            return

        from . import scheduler
        scheduler.start()