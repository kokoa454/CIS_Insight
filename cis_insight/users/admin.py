from django.contrib import admin
from .models import PreUser, User, PasswordChange

admin.site.register(PreUser)
admin.site.register(User)
admin.site.register(PasswordChange)
