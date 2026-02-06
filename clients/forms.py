from django import forms
from django.forms import ModelForm, DateTimeInput, ModelMultipleChoiceField
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Mailing, Message, Recipient


class MailingForm(ModelForm):
    """Форма для создания и редактирования рассылки."""
    recipients = ModelMultipleChoiceField(
        queryset=Recipient.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Получатели',
        required=True
    )

    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'recipients']
        widgets = {
            'start_time': DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].queryset = Message.objects.all()
        self.fields['start_time'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_time'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Проверка, что start_time не в прошлом (только при создании)
        if start_time and not self.instance.pk and start_time < timezone.now():
            raise ValidationError({
                'start_time': 'Дата начала не может быть в прошлом'
            })
        
        # Проверка, что start_time раньше end_time
        if start_time and end_time and start_time >= end_time:
            raise ValidationError({
                'start_time': 'Дата начала должна быть раньше даты окончания',
                'end_time': 'Дата окончания должна быть позже даты начала'
            })
        
        return cleaned_data


class MessageForm(ModelForm):
    """Форма для создания и редактирования сообщения."""
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
        }


class RecipientForm(ModelForm):
    """Форма для создания и редактирования получателя."""
    class Meta:
        model = Recipient
        fields = ['email', 'full_name', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }
