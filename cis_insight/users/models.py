from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser, PermissionsMixin)
from django.utils.translation import gettext_lazy as _

from core.settings import USER_ICON_URL

# 仮登録メール認証用
class PreUserManager(models.Manager):
    def create_pre_user(self, pre_user_email, verification_code):
        pre_user = self.model(
            pre_user_email = pre_user_email,
            verification_code = verification_code
        )
        pre_user.save(using=self._db)
        return pre_user

class PreUser(models.Model):
    pre_user_id = models.AutoField(
        primary_key = True,
        verbose_name = 'Pre User ID'
    )

    pre_user_email = models.EmailField(
        max_length = 255,
        unique = True,
        verbose_name = 'Pre User Email'
    )
    
    verification_code = models.CharField(
        max_length = 255,
        verbose_name = 'Verification Code'
    )
    
    pre_user_created_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = 'Pre User Created At'
    )

    is_verified = models.BooleanField(
        default = False,
        verbose_name = 'Is Verified'
    )

    objects = PreUserManager()

# 本登録用
class UserManager(BaseUserManager):
    def create_user(self, user_name, user_email, password=None, **extra_fields):
        if not user_name:
            raise ValueError('Users must have a username')
        if not user_email:
            raise ValueError('Users must have an email address')
        
        user = self.model(
            user_name = user_name,
            user_email = user_email,
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_name, user_email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(user_name, user_email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(
        primary_key = True,
        verbose_name = 'User ID'
    )
    
    user_name = models.CharField(
        max_length = 16,
        unique = True,
        verbose_name = 'User Name'
    )
    
    user_display_name = models.CharField(
        max_length = 32,
        verbose_name = 'User Display Name'
    )
    
    user_email = models.EmailField(
        max_length = 255,
        unique = True,
        verbose_name = 'User Email'
    )
    
    user_icon = models.ImageField(
        upload_to = USER_ICON_URL,
        null = True,
        blank = True,
        verbose_name = 'User Icon'
    )
    
    is_active = models.BooleanField(
        default = True,
        verbose_name = 'Is Active'
    )
    
    is_staff = models.BooleanField(
        default = False,
        verbose_name = 'Is Staff'
    )
    
    user_created_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = 'User Created At'
    )
    
    user_updated_at = models.DateTimeField(
        auto_now = True,
        verbose_name = 'User Updated At'
    )
    
    user_news_count = models.PositiveIntegerField(
        default = 0,
        verbose_name = 'User News Count'
    )
    
    user_news_referred_country = models.JSONField(
        default = list,
        verbose_name = 'User News Referred Country'
    )
    
    user_news_referred_topic = models.JSONField(
        default = list,
        verbose_name = 'User News Referred Topic'
    )

    objects = UserManager()

    USERNAME_FIELD = 'user_email'
    REQUIRED_FIELDS = ['user_name']

    def __str__(self):
        return self.user_name