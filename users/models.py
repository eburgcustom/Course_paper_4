from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Расширенная модель пользователя с подтверждением email."""
    
    # Роли пользователей
    ROLE_USER = 'user'
    ROLE_MANAGER = 'manager'
    
    ROLE_CHOICES = [
        (ROLE_USER, 'Пользователь'),
        (ROLE_MANAGER, 'Менеджер'),
    ]
    
    email = models.EmailField(
        _('Email address'),
        unique=True,
        error_messages={
            'unique': _("Пользователь с таким адресом электронной почты уже существует."),
        },
    )
    is_verified = models.BooleanField(
        _('Email verified'),
        default=False,
        help_text=_('Указывает, подтвержден ли адрес электронной почты этого пользователя.')
    )
    role = models.CharField(
        _('Роль'),
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
        help_text=_('Роль пользователя в системе')
    )
    is_active = models.BooleanField(
        _('Активен'),
        default=True,
        help_text=_('Указывает, может ли пользователь входить в систему')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.email
    
    def is_manager(self):
        """Проверяет, является ли пользователь менеджером."""
        return self.role == self.ROLE_MANAGER
    
    def is_regular_user(self):
        """Проверяет, является ли пользователем обычным пользователем."""
        return self.role == self.ROLE_USER
