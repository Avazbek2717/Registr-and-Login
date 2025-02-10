from django.contrib import admin


from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone', 'is_verified', 'is_staff', 'is_superuser')
    search_fields = ('phone',)
    list_filter = ('is_verified', 'is_staff', 'is_superuser')

