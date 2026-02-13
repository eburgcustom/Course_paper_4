from django.core.cache import cache
from django.utils import timezone
from .models import Mailing, Recipient, MailingAttempt


class StatisticsService:
    """Сервис для работы со статистикой рассылок."""

    @staticmethod
    def get_user_stats(user):
        """Получение статистики для пользователя с кешированием."""
        # Проверяем, авторизован ли пользователь
        if not user.is_authenticated:
            return {
                "total_mailings": 0,
                "active_mailings": 0,
                "unique_recipients": 0,
                "total_attempts": 0,
                "successful_attempts": 0,
                "failed_attempts": 0,
            }

        cache_key = f"user_stats_{user.id}_{user.role}"
        cached_stats = cache.get(cache_key)

        if cached_stats:
            return cached_stats

        if user.is_manager():
            stats = {
                "total_mailings": Mailing.objects.count(),
                "active_mailings": Mailing.objects.filter(
                    status__in=[Mailing.STARTED, Mailing.CREATED], end_time__gte=timezone.now()
                ).count(),
                "unique_recipients": Recipient.objects.count(),
                "total_attempts": MailingAttempt.objects.count(),
                "successful_attempts": MailingAttempt.objects.filter(status=MailingAttempt.SUCCESS).count(),
                "failed_attempts": MailingAttempt.objects.filter(status=MailingAttempt.FAILED).count(),
            }
        else:
            stats = {
                "total_mailings": Mailing.objects.filter(owner=user).count(),
                "active_mailings": Mailing.objects.filter(
                    owner=user, status__in=[Mailing.STARTED, Mailing.CREATED], end_time__gte=timezone.now()
                ).count(),
                "unique_recipients": Recipient.objects.filter(owner=user).count(),
                "total_attempts": MailingAttempt.objects.filter(mailing__owner=user).count(),
                "successful_attempts": MailingAttempt.objects.filter(
                    mailing__owner=user, status=MailingAttempt.SUCCESS
                ).count(),
                "failed_attempts": MailingAttempt.objects.filter(
                    mailing__owner=user, status=MailingAttempt.FAILED
                ).count(),
            }

        # Кешируем на 3 минуты
        cache.set(cache_key, stats, 180)
        return stats

    @staticmethod
    def clear_user_stats_cache(user):
        """Очистка кеша статистики пользователя."""
        if not user.is_authenticated:
            return
        cache_key = f"user_stats_{user.id}_{user.role}"
        cache.delete(cache_key)


class MailingService:
    """Сервис для работы с рассылками."""

    @staticmethod
    def get_user_mailings(user):
        """Получение рассылок пользователя с кешированием."""
        # Проверяем, авторизован ли пользователь
        if not user.is_authenticated:
            return Mailing.objects.none()

        cache_key = f"user_mailings_{user.id}_{user.role}"
        cached_mailings = cache.get(cache_key)

        if cached_mailings:
            return cached_mailings

        if user.is_manager():
            mailings = Mailing.objects.all()
        else:
            mailings = Mailing.objects.filter(owner=user)

        # Кешируем на 2 минуты
        cache.set(cache_key, mailings, 120)
        return mailings

    @staticmethod
    def clear_mailings_cache(user):
        """Очистка кеша рассылок пользователя."""
        if not user.is_authenticated:
            return
        cache_key = f"user_mailings_{user.id}_{user.role}"
        cache.delete(cache_key)
