from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser, PermissionsMixin)
from django.utils.translation import gettext_lazy as _
import logging

from core.settings import (USER_ICON_URL, MAXIMUM_USERNAME_LENGTH, MAXIMUM_DISPLAY_NAME_LENGTH, MAXIMUM_EMAIL_LENGTH, VALIDATION_CODE_LENGTH)

logger = logging.getLogger(__name__)

# 仮登録メール認証用
class PreUserManager(models.Manager):
    def create_pre_user(self, email, verification_code):
        pre_user = self.model(
            email = email,
            verification_code = verification_code
        )
        pre_user.save(using=self._db)
        logger.info(f'PreUser created: {pre_user}')
        return pre_user

    def get_pre_user(self, verification_code):
        try:
            pre_user = self.get(verification_code = verification_code)
            logger.info(f'PreUser retrieved: {pre_user}')
            return pre_user
        except Exception as e:
            logger.error(f'Exception in get_pre_user: {e}')
            return None

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

    objects = PreUserManager()

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
        upload_to = USER_ICON_URL,
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

# パスワード変更用
class PasswordChangeManager(models.Manager):
    def create_password_change(self, user, verification_code, **extra_fields):
        password_change = self.model(
            user = user,
            verification_code = verification_code,
            **extra_fields
        )
        password_change.save(using=self._db)
        return password_change

    def get_password_change(self, verification_code):
        try:
            password_change = self.get(verification_code = verification_code)
            return password_change
        except Exception as e:
            return None

    def verify_password_change(self, verification_code):
        try:
            password_change = self.get(verification_code = verification_code)

            if verification_code == password_change.verification_code:
                password_change.is_verified = True
                password_change.save(using=self._db)
                return password_change
            else:
                return None
        except Exception as e:
            return None

class PasswordChange(models.Model):
    password_change_id = models.AutoField(
        primary_key = True,
        verbose_name = 'Password Change ID'
    )

    user = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
        verbose_name = 'User ID'
    )
    
    verification_code = models.CharField(
        max_length = VALIDATION_CODE_LENGTH,
        verbose_name = 'Verification Code'
    )
    
    password_change_created_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = 'Password Change Created At'
    )

    is_verified = models.BooleanField(
        default = False,
        verbose_name = 'Is Verified'
    )

    objects = PasswordChangeManager()
