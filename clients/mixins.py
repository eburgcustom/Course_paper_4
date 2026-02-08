from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect


class OwnerRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки прав владельца объекта."""
    
    def test_func(self):
        """Проверяет, является ли пользователь владельцем объекта."""
        obj = self.get_object()
        return obj.owner == self.request.user
    
    def handle_no_permission(self):
        """Обрабатывает случай, когда у пользователя нет прав."""
        messages.error(self.request, 'У вас нет прав для редактирования этого объекта.')
        return redirect('clients:mailing_list')


class ManagerOrOwnerRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки прав менеджера или владельца."""
    
    def test_func(self):
        """Проверяет, является ли пользователь менеджером или владельцем."""
        obj = self.get_object()
        return (self.request.user.is_manager() or 
                obj.owner == self.request.user)
    
    def handle_no_permission(self):
        """Обрабатывает случай, когда у пользователя нет прав."""
        messages.error(self.request, 'У вас нет прав для редактирования этого объекта.')
        return redirect('clients:mailing_list')


class ManagerRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки прав менеджера."""
    
    def test_func(self):
        """Проверяет, является ли пользователь менеджером."""
        return self.request.user.is_manager()
    
    def handle_no_permission(self):
        """Обрабатывает случай, когда у пользователя нет прав."""
        messages.error(self.request, 'Эта функция доступна только менеджерам.')
        return redirect('clients:mailing_list')
