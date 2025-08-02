from rest_framework.test import APITestCase

from habits.models import Habit
from users.models import User


class HabitTestCase(APITestCase):
    """Тест кейс для проверки CRUD представлений модели 'Habit'"""

    def setUp(self) -> None:
        """Инициализация тестовых данных"""

        self.user = User.objects.create(email="testuser@example.com")
        self.habit = Habit.objects.create()
