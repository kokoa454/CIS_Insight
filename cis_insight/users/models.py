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

    def get_pre_user(self, verification_code):
        try:
            pre_user = self.get(verification_code = verification_code)
            return pre_user
        except Exception as e:
            return None

    def verify_pre_user(self, verification_code):
        try:
            pre_user = self.get(verification_code = verification_code)

            if verification_code == pre_user.verification_code:
                pre_user.is_verified = True
                pre_user.save(using=self._db)
                return pre_user
            else:
                return None
        except Exception as e:
            return None

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
    def create_user(self, user_name, user_email, user_display_name, password=None, **extra_fields):
        if not user_name:
            raise ValueError('Users must have a username')
        if not user_email:
            raise ValueError('Users must have an email address')
        
        user = self.model(
            user_name = user_name,
            user_email = user_email,
            user_display_name = user_display_name,
            **extra_fields
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def is_user_email_duplicate(self, user_email):
        try:
            if self.filter(user_email = user_email).exists():
                return True
            else:
                return False
        except Exception as e:
            return False

    def is_user_name_duplicate(self, user_name):
        try:
            if self.filter(user_name = user_name).exists():
                return True
            else:
                return False
        except Exception as e:
            return False

    def create_superuser(self, user_name, user_email, user_display_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(user_name, user_email, user_display_name, password, **extra_fields)

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

    USERNAME_FIELD = 'user_name'
    REQUIRED_FIELDS = ['user_email', 'user_display_name']

    def __str__(self):
        return self.user_name

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
        max_length = 255,
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
