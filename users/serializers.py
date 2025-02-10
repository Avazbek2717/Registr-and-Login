import random
from email.policy import default

from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from django.core.cache import cache
from .models import CustomUser  
from django.db.models import Count

import re




class UserRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=255, required=True, write_only=True)
    password1 = serializers.CharField(max_length=255, required=True, write_only=True)
    password2 = serializers.CharField(max_length=255, required=True, write_only=True)

    def validate(self, attrs):
        """Ma'lumotlarni tekshirish"""

        phone = attrs['phone']

        if not self.is_valid_phone(phone):
            raise serializers.ValidationError({"phone": "Telefon raqam noto‘g‘ri formatda!"})



        user = CustomUser.objects.filter(phone=attrs['phone'], is_verified=True).first()
        


        if user:
            raise serializers.ValidationError({"phone": "Bu raqam bilan avval ro‘yxatdan o‘tilgan"})

        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password1": "Parollar mos kelmadi!"})

        if cache.get(attrs['phone']):
            raise serializers.ValidationError({"phone": "2 daqiqadan keyin qayta urining"})
    
        return attrs

    @staticmethod
    def is_valid_phone(phone):
        """Telefon raqamni regex bilan tekshirish"""
        pattern = r"^\+998(33|55|77|88|90|91|93|94|95|97|98|99)\d{7}$"
        return re.match(pattern, phone) is not None
    


    def create(self, validated_data):
        """Foydalanuvchi yaratish"""
        phone = validated_data.pop("phone")
        password = validated_data.pop("password1")
        user = CustomUser.objects.filter(phone=phone).first()
        if user:
            user.password = password
            user.save()
        else:
            user = CustomUser.objects.create_user(phone=phone)

    
        # if created or not user.has_usable_password():
        #     user.is_active = True
        #     user.set_password(password)
        #     user.save()


        code = self.generate_random_number()
        cache.set(user.phone, code, timeout=120)
        print(f"Tasdiqlash kodi: {code}")  # Debug uchun

        return user

    @staticmethod
    def generate_random_number():
        """Tasdiqlash kodi yaratish"""
        return ''.join([str(random.randint(0, 9)) for _ in range(5)])


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=255, required=True, write_only=True)
    password = serializers.CharField(max_length=255, required=True, write_only=True)

    def validate(self, attrs):

        phone = attrs['phone']

        if not self.is_valid_phone(phone):
            raise serializers.ValidationError({"phone": "Telefon raqam noto‘g‘ri formatda!"})



        """Login ma'lumotlarini tekshirish"""
        user = CustomUser.objects.filter(phone=attrs['phone'], is_verified=True).first()

        if not user:
            raise serializers.ValidationError({"phone": "Iltimos, avval ro'yhatdan o'ting!"})

        if not user.check_password(attrs['password']):
            raise serializers.ValidationError({"password": "Parol noto‘g‘ri!"})
        

        return attrs
    @staticmethod
    def is_valid_phone(phone):
        """Telefon raqamni regex bilan tekshirish"""
        pattern = r"^\+998(33|55|77|88|90|91|93|94|95|97|98|99)\d{7}$"
        return re.match(pattern, phone) is not None







'''Agar foydalanuvchi parolni esdan chiqarsa ketadigan kodlar ketma ketligi,
birinichi yangi kod yuboramiz va u kod cache xotirda 2 minutda mobaynida saqlanadi va oxirida shu yangi kodni foydalanuciga tekshirib 
passwword change ga ruxsat beramasz

'''


class ResendVerificarionCodeSerilizer(serializers.Serializer):

    phone = serializers.CharField(max_length=255, required=True, write_only=True)

    def validate(self, attrs):

        phone = attrs['phone']
        user = CustomUser.objects.filter(phone=phone,is_verified=True)

        if not user:
            raise serializers.ValidationError({"phone": "Bu raqam bilan foydalanuvchi topilmadi yoki tasdiqlangan!"})
        if cache.get(phone):
            raise serializers.ValidationError({"phone": "Tasdiqlash kodini 2 daqiqadan keyin qayta so‘rang!"})




        return attrs
    def create(self, validated_data):
        phone = validated_data['phone']

        existing_code = cache.get(phone)

        if existing_code:
            code = existing_code
            message = "Avval yuborilgan tasdiqlsh kodidan foydalaning"
            print(code)
        else:
            code = self.generate_random_number()
            cache.set(phone,code,timeout=120)
            message = 'Yangi tasdiqlsh kodi yaratildi va yuborildi!'
            print(code)
        
        return {"message": message}
    


    
    @staticmethod
    def generate_random_number():
        """Tasdiqlash kodi yaratish"""
        return ''.join([str(random.randint(0, 9)) for _ in range(5)])
    



class SetNewPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=255, required=True, write_only=True)
    code = serializers.CharField(max_length=5, required=True, write_only=True)
    new_password1 = serializers.CharField(max_length=255, required=True, write_only=True)
    new_password2 = serializers.CharField(max_length=255, required=True, write_only=True)

    def validate(self, attrs):
        """Tasdiqlash kodini tekshirish va yangi parolni validatsiya qilish"""
        phone = attrs["phone"]
        code = attrs["code"]


        cached_code = cache.get(phone)
        if not cached_code or cached_code != code:
            raise serializers.ValidationError({"code": "Tasdiqlash kodi noto‘g‘ri yoki eskirgan!"})

    
        if attrs["new_password1"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password1": "Parollar mos kelmadi!"})

        return attrs

    def create(self, validated_data):
        """Yangi parolni saqlash"""
        phone = validated_data["phone"]
        new_password = validated_data["new_password1"]

        user = CustomUser.objects.filter(phone=phone).first()
        if not user:
            raise serializers.ValidationError({"phone": "Bu raqam bilan foydalanuvchi topilmadi!"})

        user.set_password(new_password)
        user.save()

    
        cache.delete(phone)

        return {"message": "Parol muvaffaqiyatli o‘zgartirildi!"}



class ChangePasswordInsideSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=5, required=False, write_only=True)
    old_password = serializers.CharField(max_length=255, required=True, write_only=True)
    new_password = serializers.CharField(max_length=255, required=True, write_only=True)

    def validate(self, attrs):

        request = self.context['request']
        user = request.user
        cache_code = cache.get(f'change_{user.phone}')

        if attrs.get('code'):

            if not cache_code:
                raise serializers.ValidationError({"code": "Kod mavjud emas"})
            print(attrs['code'], cache_code)
            if attrs['code'] != str(cache_code):
                raise serializers.ValidationError({"code": "Kod xato kiritildi"})


        if not check_password(attrs['old_password'], user.password):
            raise serializers.ValidationError({"old_password": "Eski parol noto‘g‘ri!"})

        return attrs


    def create(self, validated_data):
        user = self.context['request'].user
        
        if validated_data.get("code"):
            user.password = validated_data.get("new_password")
            user.save()
        else:
            cache.set("change_" + user.phone, 12345, timeout=120)
            raise serializers.ValidationError({"code": "SMS kodni kiriting"})

        return validated_data



