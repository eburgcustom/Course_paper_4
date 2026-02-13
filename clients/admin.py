from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Mailing, Message, Recipient, MailingAttempt, MailingLog


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    """Админ-панель для управления получателями."""

    list_display = ("full_name", "email", "created_at", "mailings_count")
    list_filter = ("created_at",)
    search_fields = ("full_name", "email", "comment")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "mailings_count_display")

    fieldsets = (
        ("Основная информация", {"fields": ("full_name", "email", "comment")}),
        (
            "Системная информация",
            {"fields": ("created_at", "updated_at", "mailings_count_display"), "classes": ("collapse",)},
        ),
    )

    def mailings_count(self, obj):
        """Количество рассылок для получателя."""
        return obj.mailings.count()

    mailings_count.short_description = "Кол-во рассылок"

    def mailings_count_display(self, obj):
        """Отображение количества рассылок в форме редактирования."""
        count = obj.mailings.count()
        return mark_safe(f"<strong>{count}</strong> рассылок")

    mailings_count_display.short_description = "Количество рассылок"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Админ-панель для управления сообщениями."""

    list_display = ("subject", "body_preview", "created_at", "mailings_count")
    list_filter = ("created_at",)
    search_fields = ("subject", "body")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "mailings_count_display")

    fieldsets = (
        ("Содержание сообщения", {"fields": ("subject", "body")}),
        (
            "Системная информация",
            {"fields": ("created_at", "updated_at", "mailings_count_display"), "classes": ("collapse",)},
        ),
    )

    def body_preview(self, obj):
        """Предпросмотр тела письма."""
        return obj.body[:100] + "..." if len(obj.body) > 100 else obj.body

    body_preview.short_description = "Тело письма"

    def mailings_count(self, obj):
        """Количество рассылок с этим сообщением."""
        return obj.mailings.count()

    mailings_count.short_description = "Кол-во рассылок"

    def mailings_count_display(self, obj):
        """Отображение количества рассылок в форме редактирования."""
        count = obj.mailings.count()
        return mark_safe(f"<strong>{count}</strong> рассылок")

    mailings_count_display.short_description = "Количество рассылок"


class MailingAttemptInline(admin.TabularInline):
    """Встраиваемая панель для попыток рассылки."""

    model = MailingAttempt
    extra = 0
    readonly_fields = ("attempt_time", "status", "server_response")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Админ-панель для управления рассылками."""

    list_display = (
        "id",
        "message_subject",
        "status_display",
        "start_time",
        "end_time",
        "recipients_count",
        "created_at",
    )
    list_filter = ("status", "created_at", "start_time", "end_time")
    search_fields = ("message__subject", "message__body", "recipients__full_name", "recipients__email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "status_display", "recipients_list")
    filter_horizontal = ("recipients",)
    inlines = [MailingAttemptInline]

    fieldsets = (
        ("Основные параметры", {"fields": ("message", "recipients", "status_display")}),
        ("Временные настройки", {"fields": ("start_time", "end_time")}),
        (
            "Информация о рассылке",
            {"fields": ("created_at", "updated_at", "recipients_list"), "classes": ("collapse",)},
        ),
    )

    def message_subject(self, obj):
        """Тема сообщения."""
        return obj.message.subject

    message_subject.short_description = "Тема письма"

    def status_display(self, obj):
        """Цветной индикатор статуса."""
        colors = {
            "created": "#ffc107",  # желтый
            "started": "#28a745",  # зеленый
            "completed": "#6c757d",  # серый
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_display.short_description = "Статус"

    def recipients_count(self, obj):
        """Количество получателей."""
        return obj.recipients.count()

    recipients_count.short_description = "Получателей"

    def recipients_list(self, obj):
        """Список получателей для просмотра."""
        recipients = obj.recipients.all()
        if not recipients:
            return "Нет получателей"

        recipient_list = "<br>".join([f"• {r.full_name} &lt;{r.email}&gt;" for r in recipients])
        return mark_safe(f'<div style="max-height: 200px; overflow-y: auto;">{recipient_list}</div>')

    recipients_list.short_description = "Список получателей"

    def get_queryset(self, request):
        """Оптимизация запросов."""
        queryset = super().get_queryset(request)
        return queryset.select_related("message").prefetch_related("recipients")


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    """Админ-панель для управления попытками рассылки."""

    list_display = ("mailing_info", "status_display", "attempt_time", "server_response_preview")
    list_filter = ("status", "attempt_time", "mailing")
    search_fields = ("mailing__message__subject", "server_response")
    ordering = ("-attempt_time",)
    readonly_fields = ("attempt_time", "mailing", "status", "server_response")

    def mailing_info(self, obj):
        """Информация о рассылке."""
        return f"#{obj.mailing.id} - {obj.mailing.message.subject}"

    mailing_info.short_description = "Рассылка"

    def status_display(self, obj):
        """Цветной индикатор статуса."""
        colors = {
            "success": "#28a745",  # зеленый
            "failed": "#dc3545",  # красный
        }
        color = colors.get(obj.status, "#6c757d")
        status_text = "Успешно" if obj.status == "success" else "Ошибка"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            status_text,
        )

    status_display.short_description = "Статус"

    def server_response_preview(self, obj):
        """Предпросмотр ответа сервера."""
        if not obj.server_response:
            return "-"
        return obj.server_response[:100] + "..." if len(obj.server_response) > 100 else obj.server_response

    server_response_preview.short_description = "Ответ сервера"


@admin.register(MailingLog)
class MailingLogAdmin(admin.ModelAdmin):
    """Админ-панель для управления логами рассылок."""

    list_display = ("mailing_info", "recipient_email", "status_display", "created_at", "server_response_preview")
    list_filter = ("status", "created_at", "mailing")
    search_fields = ("mailing__message__subject", "recipient_email", "server_response")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "mailing", "recipient_email", "status", "server_response")

    def mailing_info(self, obj):
        """Информация о рассылке."""
        return f"#{obj.mailing.id} - {obj.mailing.message.subject}"

    mailing_info.short_description = "Рассылка"

    def status_display(self, obj):
        """Цветной индикатор статуса."""
        colors = {
            "success": "#28a745",  # зеленый
            "error": "#dc3545",  # красный
        }
        color = colors.get(obj.status, "#6c757d")
        status_text = "Успешно" if obj.status == "success" else "Ошибка"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            status_text,
        )

    status_display.short_description = "Статус"

    def server_response_preview(self, obj):
        """Предпросмотр ответа сервера."""
        if not obj.server_response:
            return "-"
        return obj.server_response[:100] + "..." if len(obj.server_response) > 100 else obj.server_response

    server_response_preview.short_description = "Ответ сервера"


# Настройка заголовка админ-панели
admin.site.site_header = "Управление рассылками"
admin.site.site_title = "Рассылки"
admin.site.index_title = "Панель управления рассылками"
