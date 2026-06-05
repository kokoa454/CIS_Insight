import logging

from core.settings import (MAXIMUM_DISPLAY_NAME_LENGTH, MAXIMUM_EMAIL_LENGTH,
                           MAXIMUM_USERNAME_LENGTH, USER_ICON_DIR,
                           VALIDATION_CODE_LENGTH)
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

# 仮登録メール認証用
class PreUser(models.Model):
    id = models.AutoField(
        primary_key = True,
        verbose_name = 'ID'
    )

    email = models.EmailField(
        max_length = MAXIMUM_EMAIL_LENGTH,
        unique = True,
        verbose_name = 'Email'
    )
    
    verification_code = models.CharField(
        max_length = VALIDATION_CODE_LENGTH,
        unique = True,
        verbose_name = 'Verification Code'
    )
    
    created_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = 'Created At'
    )

    is_expired = models.BooleanField(
        default = False,
        verbose_name = 'Is Expired'
    )

    def __str__(self):
        return self.email

# 本登録用
class UserManager(BaseUserManager):
    def create_user(self, username, email, display_name, password = None, **extra_fields):
        if not username:
            raise ValueError('Users must have a username')
        if not email:
            raise ValueError('Users must have an email address')
        
        user = self.model(
            username = username,
            email = email,
            display_name = display_name,
            **extra_fields
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, display_name, password = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, display_name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(
        primary_key = True,
        verbose_name = 'ID'
    )
    
    username = models.CharField(
        max_length = MAXIMUM_USERNAME_LENGTH,
        unique = True,
        verbose_name = 'Username'
    )
    
    display_name = models.CharField(
        max_length = MAXIMUM_DISPLAY_NAME_LENGTH,
        verbose_name = 'Display Name'
    )
    
    email = models.EmailField(
        max_length = MAXIMUM_EMAIL_LENGTH,
        unique = True,
        verbose_name = 'Email'
    )
    
    icon = models.ImageField(
        upload_to = USER_ICON_DIR,
        null = True,
        blank = True,
        verbose_name = 'Icon'
    )
    
    is_active = models.BooleanField(
        default = True,
        verbose_name = 'Is Active'
    )
    
    is_staff = models.BooleanField(
        default = False,
        verbose_name = 'Is Staff'
    )
    
    created_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = 'Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now = True,
        verbose_name = 'Updated At'
    )
    
    news_count = models.PositiveIntegerField(
        default = 0,
        verbose_name = 'News Count'
    )
    
    news_referred_country = models.JSONField(
        default = list,
        verbose_name = 'News Referred Country'
    )
    
    news_referred_topic = models.JSONField(
        default = list,
        verbose_name = 'News Referred Topic'
    )

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'display_name']

    def __str__(self):
        return self.username

# メール変更用
class EmailChange(models.Model):
    id = models.AutoField(
        primary_key = True,
        verbose_name = 'ID'
    )

    user = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
        verbose_name = 'User'
    )
    
    verification_code = models.CharField(
        max_length = VALIDATION_CODE_LENGTH,
        unique = True,
        verbose_name = 'Verification Code'
    )

    new_email = models.EmailField(
        max_length = MAXIMUM_EMAIL_LENGTH,
        verbose_name = 'New Email'
    )
    
    created_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = 'Created At'
    )
    
    is_expired = models.BooleanField(
        default = False,
        verbose_name = 'Is Expired'
    )

    def __str__(self):
        return self.user.username
