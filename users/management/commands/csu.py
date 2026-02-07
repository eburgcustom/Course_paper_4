from django.core.management.base import BaseCommand
from users.models import CustomUser
from decouple import config


class Command(BaseCommand):
    help = "Создание суперпользователя"

    def handle(self, *args, **options):
        try:
            email = config('EMAIL_HOST_USER')
            password = config('PASSWORD_FOR_SUPER_USER')

            if not email or not password:
                self.stdout.write(
                    self.style.ERROR('EMAIL_HOST_USER и PASSWORD_FOR_SUPER_USER должны быть заданы в .env')
                )
                return

            # Проверяем, не существует ли уже суперпользователь
            if CustomUser.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'Пользователь с email {email} уже существует')
                )
                return

            # Создаем суперпользователя
            user = CustomUser.objects.create_superuser(
                email=email,
                username='admin',  # или можно использовать email как username
                password=password
            )

            self.stdout.write(
                self.style.SUCCESS(f'Суперпользователь {email} успешно создан')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при создании суперпользователя: {e}')
            )
