from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.conf import settings

from .models import Mailing, Message, Recipient, MailingAttempt
from .forms import MailingForm, MessageForm, RecipientForm
from .mixins import ManagerOrOwnerRequiredMixin
from .services import StatisticsService, MailingService


def home(request):
    # Получаем статистику через сервис
    stats = StatisticsService.get_user_stats(request.user)

    # Получаем последние рассылки
    latest_mailings = Mailing.objects.all().order_by("-created_at")[:5]

    context = {
        **stats,
        "latest_mailings": latest_mailings,
    }
    return render(request, "clients/home.html", context)


class MailingListView(LoginRequiredMixin, ListView):
    """Список всех рассылок."""

    model = Mailing
    template_name = "clients/mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 10

    def get_queryset(self):
        """Фильтруем рассылки через сервис."""
        return MailingService.get_user_mailings(self.request.user)


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание новой рассылки."""

    model = Mailing
    form_class = MailingForm
    template_name = "clients/mailing_form.html"
    success_url = reverse_lazy("clients:mailing_list")

    def form_valid(self, form):
        form.instance.status = Mailing.CREATED
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Рассылка успешно создана!")
        # Очищаем кеш через сервис
        StatisticsService.clear_user_stats_cache(self.request.user)
        MailingService.clear_mailings_cache(self.request.user)
        return response


class MailingUpdateView(ManagerOrOwnerRequiredMixin, UpdateView):
    """Редактирование рассылки."""

    model = Mailing
    form_class = MailingForm
    template_name = "clients/mailing_form.html"

    def get_success_url(self):
        messages.success(self.request, "Рассылка успешно обновлена!")
        # Очищаем кеш через сервис
        StatisticsService.clear_user_stats_cache(self.request.user)
        MailingService.clear_mailings_cache(self.request.user)
        return reverse("clients:mailing_detail", kwargs={"pk": self.object.pk})


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр рассылки."""

    model = Mailing
    template_name = "clients/mailing_detail.html"
    context_object_name = "mailing"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()  # ← пересчёт и сохранение статуса
        return obj


@require_POST
def send_mailing_now(request, pk):
    """Отправка рассылки немедленно."""
    mailing = get_object_or_404(Mailing, pk=pk)

    # Проверяем права доступа
    if not (request.user.is_manager() or mailing.owner == request.user):
        messages.error(request, "У вас нет прав для отправки этой рассылки.")
        return redirect("clients:mailing_detail", pk=mailing.pk)

    if mailing.status == Mailing.STARTED:
        return JsonResponse({"status": "error", "message": "Рассылка уже запущена"}, status=400)

    # Обновляем статус рассылки
    mailing.status = Mailing.STARTED
    mailing.save()

    # Отправляем письма
    success_count = 0
    error_count = 0

    for recipient in mailing.recipients.all():
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            MailingAttempt.objects.create(
                mailing=mailing, status=MailingAttempt.SUCCESS, server_response="Успешно отправлено"
            )
            success_count += 1
        except Exception as e:
            MailingAttempt.objects.create(mailing=mailing, status=MailingAttempt.FAILED, server_response=str(e))
            error_count += 1

    mailing.status = Mailing.COMPLETED
    mailing.save()

    messages.success(request, f"Рассылка завершена. Успешно: {success_count}, Ошибок: {error_count}")
    return redirect("clients:mailing_detail", pk=mailing.pk)


# Остальные представления остаются без изменений
class MessageListView(LoginRequiredMixin, ListView):
    """Список сообщений."""

    model = Message
    template_name = "clients/message_list.html"
    context_object_name = "messages"
    paginate_by = 10

    def get_queryset(self):
        """Фильтруем сообщения в зависимости от роли пользователя."""
        if self.request.user.is_manager():
            return Message.objects.all()
        return Message.objects.filter(owner=self.request.user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание нового сообщения."""

    model = Message
    form_class = MessageForm
    template_name = "clients/message_form.html"
    success_url = reverse_lazy("clients:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Сообщение успешно создано!")
        return response


class MessageUpdateView(ManagerOrOwnerRequiredMixin, UpdateView):
    """Редактирование сообщения."""

    model = Message
    form_class = MessageForm
    template_name = "clients/message_form.html"
    success_url = reverse_lazy("clients:message_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Сообщение успешно обновлено!")
        return response


class RecipientListView(LoginRequiredMixin, ListView):
    """Список получателей."""

    model = Recipient
    template_name = "clients/recipient_list.html"
    context_object_name = "recipients"
    paginate_by = 20

    def get_queryset(self):
        """Фильтруем получателей в зависимости от роли пользователя."""
        if self.request.user.is_manager():
            return Recipient.objects.all()
        return Recipient.objects.filter(owner=self.request.user)


class RecipientCreateView(LoginRequiredMixin, CreateView):
    """Добавление нового получателя."""

    model = Recipient
    form_class = RecipientForm
    template_name = "clients/recipient_form.html"
    success_url = reverse_lazy("clients:recipient_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Получатель успешно создан!")
        return response

    def get_success_url(self):
        """Сохраняем параметр next при перенаправлении."""
        next_url = self.request.GET.get("next")
        if next_url:
            return f"{self.success_url}?next={next_url}"
        return self.success_url


class RecipientUpdateView(ManagerOrOwnerRequiredMixin, UpdateView):
    """Редактирование получателя."""

    model = Recipient
    form_class = RecipientForm
    template_name = "clients/recipient_form.html"
    success_url = reverse_lazy("clients:recipient_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Получатель успешно обновлен!")
        return response

    def get_success_url(self):
        """Сохраняем параметр next при перенаправлении."""
        next_url = self.request.GET.get("next")
        if next_url:
            return f"{self.success_url}?next={next_url}"
        return self.success_url


class RecipientDeleteView(ManagerOrOwnerRequiredMixin, DeleteView):
    """Удаление получателя."""

    model = Recipient
    template_name = "clients/recipient_confirm_delete.html"
    success_url = reverse_lazy("clients:recipient_list")

    def get_success_url(self):
        """Сохраняем параметр next при перенаправлении."""
        next_url = self.request.GET.get("next")
        if next_url:
            return f"{self.success_url}?next={next_url}"
        return self.success_url

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Получатель успешно удален!")
        return super().delete(request, *args, **kwargs)


class MessageDeleteView(ManagerOrOwnerRequiredMixin, DeleteView):
    """Удаление сообщения."""

    model = Message
    template_name = "clients/message_confirm_delete.html"
    success_url = reverse_lazy("clients:message_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Сообщение успешно удалено!")
        return super().delete(request, *args, **kwargs)


class MailingDeleteView(ManagerOrOwnerRequiredMixin, DeleteView):
    """Удаление рассылки."""

    model = Mailing
    template_name = "clients/mailing_confirm_delete.html"
    success_url = reverse_lazy("clients:mailing_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Рассылка успешно удалена!")
        return super().delete(request, *args, **kwargs)
