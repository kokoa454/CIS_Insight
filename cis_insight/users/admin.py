from django.contrib import admin
from .models import PreUser, User, PasswordChange, EmailChange

admin.site.register(PreUser)
admin.site.register(User)
admin.site.register(PasswordChange)
admin.site.register(EmailChange)
