from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken
from phonenumber_field.modelfields import PhoneNumberField



class CustomUserManager(BaseUserManager):
    """Foydalanuvchilarni telefon raqam orqali yaratish uchun Manager"""

    def create_user(self, phone, password=None, **extra_fields):
        """Oddiy foydalanuvchi yaratish"""
        if not phone:
            raise ValueError("Telefon raqam kiritilishi shart!")

        extra_fields.setdefault("is_active", True)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        """Superuser yaratish"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(phone, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    phone = models.CharField(
        max_length=255, unique=True, verbose_name="Telefon raqam"
    )
    is_verified = models.BooleanField(default=False, verbose_name="Tasdiqlangan")

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def str(self):
        return str(self.phone)

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }