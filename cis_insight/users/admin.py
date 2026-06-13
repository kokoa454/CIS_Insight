from django.contrib import admin
from .models import PreUser, User, EmailChange, PasswordReset

admin.site.register(PreUser)
admin.site.register(User)
admin.site.register(EmailChange)
admin.site.register(PasswordReset)
