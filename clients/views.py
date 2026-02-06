from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Mailing, Message, Recipient
from .forms import MailingForm, MessageForm, RecipientForm


def home(request):
    total_mailings = Mailing.objects.count()
    active_mailings = Mailing.objects.filter(
        status=Mailing.STARTED,
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    ).count()

    unique_recipients = Recipient.objects.filter(
        mailings__isnull=False
    ).distinct().count()

    latest_mailings = Mailing.objects.order_by('-created_at')[:5]

    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'unique_recipients': unique_recipients,
        'latest_mailings': latest_mailings,
    }
    return render(request, 'clients/home.html', context)


class MailingListView(LoginRequiredMixin, ListView):
    """Список всех рассылок."""
    model = Mailing
    template_name = 'clients/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание новой рассылки."""
    model = Mailing
    form_class = MailingForm
    template_name = 'clients/mailing_form.html'
    success_url = reverse_lazy('mailing_list')

    def form_valid(self, form):
        form.instance.status = Mailing.CREATED
        response = super().form_valid(form)
        messages.success(self.request, 'Рассылка успешно создана!')
        return response


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование рассылки."""
    model = Mailing
    form_class = MailingForm
    template_name = 'clients/mailing_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Рассылка успешно обновлена!')
        return reverse('mailing_detail', kwargs={'pk': self.object.pk})


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр рассылки."""
    model = Mailing
    template_name = 'clients/mailing_detail.html'
    context_object_name = 'mailing'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()  # ← пересчёт и сохранение статуса
        return obj


@require_POST
def send_mailing_now(request, pk):
    """Отправка рассылки немедленно (синхронно)."""
    mailing = get_object_or_404(Mailing, pk=pk)

    if mailing.status == Mailing.STARTED:
        return JsonResponse(
            {'status': 'error', 'message': 'Рассылка уже запущена'},
            status=400
        )

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
                mailing=mailing,
                status=MailingAttempt.SUCCESS,
                server_response='Успешно отправлено'
            )
            success_count += 1
        except Exception as e:
            MailingAttempt.objects.create(
                mailing=mailing,
                status=MailingAttempt.FAILED,
                server_response=str(e)
            )
            error_count += 1

    mailing.status = Mailing.COMPLETED
    mailing.save()

    return JsonResponse({
        'status': 'success',
        'message': f'Рассылка завершена. Успешно: {success_count}, Ошибок: {error_count}'
    })


# Остальные представления остаются без изменений
class MessageListView(LoginRequiredMixin, ListView):
    """Список сообщений."""
    model = Message
    template_name = 'clients/message_list.html'
    context_object_name = 'messages'
    paginate_by = 10


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание нового сообщения."""
    model = Message
    form_class = MessageForm
    template_name = 'clients/message_form.html'
    success_url = reverse_lazy('message_list')


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование сообщения."""
    model = Message
    form_class = MessageForm
    template_name = 'clients/message_form.html'
    success_url = reverse_lazy('message_list')


class RecipientListView(LoginRequiredMixin, ListView):
    """Список получателей."""
    model = Recipient
    template_name = 'clients/recipient_list.html'
    context_object_name = 'recipients'
    paginate_by = 20


class RecipientCreateView(LoginRequiredMixin, CreateView):
    """Добавление нового получателя."""
    model = Recipient
    form_class = RecipientForm
    template_name = 'clients/recipient_form.html'
    success_url = reverse_lazy('recipient_list')


class RecipientUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование получателя."""
    model = Recipient
    form_class = RecipientForm
    template_name = 'clients/recipient_form.html'
    success_url = reverse_lazy('recipient_list')


class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление получателя."""
    model = Recipient
    template_name = 'clients/recipient_confirm_delete.html'
    success_url = reverse_lazy('recipient_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Получатель успешно удален!')
        return super().delete(request, *args, **kwargs)


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление сообщения."""
    model = Message
    template_name = 'clients/message_confirm_delete.html'
    success_url = reverse_lazy('message_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Сообщение успешно удалено!')
        return super().delete(request, *args, **kwargs)


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление рассылки."""
    model = Mailing
    template_name = 'clients/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Рассылка успешно удалена!')
        return super().delete(request, *args, **kwargs)
