from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Расширенная модель пользователя с подтверждением email."""
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.email
