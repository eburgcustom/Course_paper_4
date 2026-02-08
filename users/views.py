from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings

from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordResetForm, CustomSetPasswordForm
from .models import CustomUser
from .tokens import account_activation_token


class CustomLoginView(LoginView):
    """Представление входа пользователя."""

    form_class = CustomAuthenticationForm
    template_name = "users/login.html"

    def get_success_url(self):
        return reverse_lazy("clients:home")


class CustomLogoutView(LogoutView):
    """Представление выхода пользователя."""

    next_page = reverse_lazy("users:login")


class CustomPasswordResetView(PasswordResetView):
    """Представление восстановления пароля."""

    form_class = CustomPasswordResetForm
    template_name = "users/password_reset.html"
    email_template_name = "users/password_reset_email.html"
    subject_template_name = "users/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")

    def form_valid(self, form):
        messages.success(self.request, "Инструкции по восстановлению пароля отправлены на ваш email.")
        return super().form_valid(form)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Представление установки нового пароля."""

    form_class = CustomSetPasswordForm
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        messages.success(self.request, "Пароль успешно изменен. Теперь вы можете войти.")
        return super().form_valid(form)


def register(request):
    """Представление регистрации пользователя."""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Деактивируем пользователя до подтверждения email
            user.save()

            # Отправка письма с подтверждением
            token = account_activation_token.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            current_site = request.get_host()
            mail_subject = "Активация аккаунта"

            # Простое текстовое сообщение
            activation_link = f"http://{current_site}/activate/{uid}/{token}/"
            message = f"""Здравствуйте, {user.username}!

Спасибо за регистрацию в нашей системе рассылок.

Пожалуйста, перейдите по ссылке ниже, чтобы активировать ваш аккаунт:
{activation_link}

Если вы не регистрировались в нашей системе, просто проигнорируйте это письмо.

С уважением,
Команда системы рассылок"""

            try:
                send_mail(
                    mail_subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, "Регистрация прошла успешно! Проверьте ваш email для активации аккаунта.")
                return redirect("users:login")
            except Exception as e:
                messages.error(request, f"Ошибка при отправке письма: {e}")
                user.delete()  # Удаляем пользователя, если не удалось отправить письмо
                return redirect("users:register")
    else:
        form = CustomUserCreationForm()

    return render(request, "users/register.html", {"form": form})


def activate(request, uidb64, token):
    """Представление активации аккаунта."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.is_verified = True
        user.save()
        messages.success(request, "Ваш аккаунт успешно активирован! Теперь вы можете войти.")
        return redirect("users:login")
    else:
        messages.error(request, "Ссылка активации недействительна!")
        return redirect("users:register")


@login_required
def profile(request):
    """Представление профиля пользователя."""
    return render(request, "users/profile.html", {"user": request.user})
