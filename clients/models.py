from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings


class Mailing(models.Model):
    """Модель рассылки."""

    # Статусы рассылки
    COMPLETED = "completed"
    CREATED = "created"
    STARTED = "started"

    STATUS_CHOICES = [
        (COMPLETED, "Завершена"),
        (CREATED, "Создана"),
        (STARTED, "Запущена"),
    ]

    start_time = models.DateTimeField("Время первой отправки")
    end_time = models.DateTimeField("Время окончания отправки")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default=CREATED)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Владелец", related_name="mailings"
    )
    message = models.ForeignKey("Message", on_delete=models.CASCADE, verbose_name="Сообщение", related_name="mailings")
    recipients = models.ManyToManyField("Recipient", verbose_name="Получатели", related_name="mailings")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Рассылка {self.id} - {self.get_status_display()}"

    def clean(self):
        """Валидация модели."""
        errors = {}

        # Проверка, что start_time не в прошлом
        if self.start_time and self.start_time < timezone.now():
            errors["start_time"] = "Дата начала не может быть в прошлом"

        # Проверка, что start_time раньше end_time
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors["start_time"] = "Дата начала должна быть раньше даты окончания"
            errors["end_time"] = "Дата окончания должна быть позже даты начала"

        if errors:
            raise ValidationError(errors)

    def update_status(self):
        """Динамическое обновление статуса рассылки."""
        current_time = timezone.now()
        new_status = self.status

        if current_time < self.start_time:
            new_status = self.CREATED
        elif self.start_time <= current_time <= self.end_time:
            new_status = self.STARTED
        else:
            new_status = self.COMPLETED

        # Сохраняем только если статус изменился
        if new_status != self.status:
            self.status = new_status
            self.save(update_fields=["status"])


class Recipient(models.Model):
    """Модель получателя рассылки."""

    email = models.EmailField(_("Email"), max_length=255, unique=True, help_text=_("Email получателя"))
    full_name = models.CharField(_("ФИО"), max_length=255, help_text=_("Полное имя получателя"))
    comment = models.TextField(_("Комментарий"), blank=True, help_text=_("Дополнительная информация о получателе"))
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Владелец", related_name="recipients"
    )
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)

    class Meta:
        verbose_name = _("Получатель")
        verbose_name_plural = _("Получатели")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class Message(models.Model):
    """Модель сообщения для рассылки."""

    subject = models.CharField("Тема письма", max_length=255, help_text="Введите тему письма")
    body = models.TextField("Тело письма", help_text="Введите текст письма")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Владелец", related_name="messages"
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject


class MailingLog(models.Model):
    """Модель для хранения логов рассылок."""

    STATUS_CHOICES = [
        ("success", "Успешно"),
        ("error", "Ошибка"),
    ]

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name="logs", verbose_name="Рассылка")
    recipient_email = models.EmailField("Email получателя")
    status = models.CharField("Статус", max_length=10, choices=STATUS_CHOICES)
    server_response = models.TextField("Ответ сервера", blank=True, null=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Лог рассылки"
        verbose_name_plural = "Логи рассылок"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.mailing} - {self.recipient_email} - {self.get_status_display()}"


class MailingAttempt(models.Model):
    SUCCESS = "success"
    FAILED = "failed"

    STATUS_CHOICES = [
        (SUCCESS, "Успешно"),
        (FAILED, "Не успешно"),
    ]

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name="attempts", verbose_name="Рассылка")
    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Статус")
    server_response = models.TextField(verbose_name="Ответ сервера", blank=True, null=True)

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"
        ordering = ["-attempt_time"]
