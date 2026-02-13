from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Админ-панель для кастомной модели пользователя."""

    list_display = ("email", "username", "first_name", "last_name", "role", "is_verified", "is_staff", "is_active")
    list_filter = ("role", "is_verified", "is_staff", "is_active", "date_joined")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions", "role"),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Email verification"), {"fields": ("is_verified",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "role"),
            },
        ),
    )

    readonly_fields = ("last_login", "date_joined")

    actions = ["block_users", "unblock_users"]

    def block_users(self, request, queryset):
        """Блокировка выбранных пользователей."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} пользователей заблокировано.")

    block_users.short_description = "Заблокировать выбранных пользователей"

    def unblock_users(self, request, queryset):
        """Разблокировка выбранных пользователей."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} пользователей разблокировано.")

    unblock_users.short_description = "Разблокировать выбранных пользователей"
