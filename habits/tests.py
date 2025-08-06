import json
from datetime import datetime, time, timedelta
from io import StringIO
from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from django_celery_beat.models import PeriodicTask
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from config import settings
from habits.models import Habit
from habits.services import send_telegram_message, setup_habit_reminder
from habits.tasks import send_information, send_reminder
from users.models import User


class HabitTestCase(APITestCase):
    """Тест кейс для проверки CRUD представлений модели 'Habit'"""

    def setUp(self) -> None:
        """Инициализация тестовых данных"""

        self.user = User.objects.create(email="testuser@example.com")
        self.reward_habit = Habit.objects.create(user=self.user, is_pleasant=True, action="some pleasant action")
        self.habit = Habit.objects.create(
            user=self.user,
            action="some useful action",
            frequency_days=1,
            lead_time=timedelta(minutes=2),
            time=time(18, 10),
            reward_habit=self.reward_habit,
        )
        self.client.force_authenticate(user=self.user)

    def test_habit_retrieve(self) -> None:
        """Тест получения деталей привычки"""

        url = reverse("habits:habits-detail", args=(self.habit.pk,))
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data.get("action"), self.habit.action)
        self.assertEqual(data.get("frequency_days"), self.habit.frequency_days)
        self.assertEqual(data.get("lead_time"), "00:02:00")
        self.assertEqual(False, self.habit.is_pleasant)
        self.assertEqual(data.get("reward_habit"), self.habit.reward_habit.pk)

    def test_habit_create(self) -> None:
        """Тест создания новой привычки"""

        url = reverse("habits:habits-list")
        data = {
            "user": self.user.pk,
            "action": "какое-то полезное действие",
            "reward_habit": self.reward_habit.pk,
            "frequency_days": 1,
            "lead_time": "00:01:50",
            "time": "13:00:00",
            "is_pleasant": False,
        }
        response = self.client.post(url, data, format="json")
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.all().count(), 3)

    def test_habit_update(self) -> None:
        """Тест обновления деталей привычки"""

        url = reverse("habits:habits-detail", args=(self.habit.pk,))
        data = {
            "action": "new useful action",
        }
        response = self.client.patch(url, data, format="json")
        print(response.content)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data.get("action"), "new useful action")

    def test_habit_delete(self) -> None:
        """Тест удаления привычки"""

        url = reverse("habits:habits-detail", args=(self.habit.pk,))

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Habit.DoesNotExist):
            Habit.objects.get(pk=self.habit.pk)

    def test_habit_list(self) -> None:
        """Тест списка привычек"""

        url = reverse("habits:habits-list")
        response = self.client.get(url)
        data = response.json()

        reward_habit = self.reward_habit
        habit = self.habit

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Habit.objects.all().count(), 2)
        self.assertEqual(len(data["results"]), 2)

        reward_habit_data = data["results"][0]
        self.assertEqual(reward_habit_data["id"], reward_habit.pk)
        self.assertEqual(reward_habit_data["user"], reward_habit.user.email)
        self.assertEqual(reward_habit_data["action"], reward_habit.action)
        self.assertEqual(reward_habit_data["is_pleasant"], True)

        habit_data = data["results"][1]
        self.assertEqual(habit_data["id"], habit.pk)
        self.assertEqual(habit_data["user"], habit.user.email)
        self.assertEqual(habit_data["action"], habit.action)
        self.assertEqual(habit_data["is_pleasant"], False)
        self.assertEqual(habit_data["reward_habit"], self.reward_habit.pk)

    @parameterized.expand(
        [
            (8, "'frequency_days' не может быть больше 7!"),
            (0, "'frequency_days' не может быть меньше 1!"),
            ("a", "'frequency_days' должно быть числом от 1 до 7!"),
            (-5, "'frequency_days' не может быть меньше 1!"),
        ]
    )
    def test_habit_create_invalid_frequency_days(self, invalid_value, expected_error) -> None:
        """Тест создания привычки с невалидным полем 'frequency_days'"""

        url = reverse("habits:habits-list")
        invalid_data = {
            "user": self.user,
            "action": "полезное действие",
            "reward_habit": self.reward_habit.pk,
            "frequency_days": invalid_value,
        }
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("frequency_days", response.data)
        self.assertEqual(response.data["frequency_days"][0], expected_error)

    @parameterized.expand(
        [
            (8, "'frequency_days' не может быть больше 7!"),
            (0, "'frequency_days' не может быть меньше 1!"),
            ("a", "'frequency_days' должно быть числом от 1 до 7!"),
            (-5, "'frequency_days' не может быть меньше 1!"),
        ]
    )
    def test_habit_update_invalid_frequency_days(self, invalid_value, expected_error) -> None:
        """Тест обновления привычки с невалидным полем 'frequency_days'"""

        url = reverse("habits:habits-detail", args=(self.habit.pk,))
        invalid_data = {"frequency_days": invalid_value}

        response = self.client.patch(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("frequency_days", response.data)
        self.assertEqual(response.data["frequency_days"][0], expected_error)

    @parameterized.expand(
        [
            ("16-00", "Введите время выполнения в формате ЧЧ:ММ:СС или ММ:СС (максимум 2 минуты)!"),
            (None, "Это поле не может быть пустым (null)!"),
        ]
    )
    def test_habit_create_invalid_lead_time_serializers(self, invalid_value, expected_error) -> None:
        """Тест обновления привычки с невалидным полем 'lead_time'(проверка в сериализаторе)"""

        url = reverse("habits:habits-list")
        invalid_data = {
            "user": self.user.email,
            "action": "полезное действие",
            "reward_habit": self.reward_habit.pk,
            "frequency_days": 1,
            "time": time(12, 0),
            "lead_time": invalid_value,
        }
        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lead_time", response.data)
        self.assertEqual(response.data["lead_time"][0], expected_error)

    @parameterized.expand(
        [
            (timedelta(minutes=12), "'lead_time': Время выполнения не должно превышать 2 минуты!"),
            ("", "'lead_time': Время выполнения не должно быть нулевое или отрицательное!"),
        ]
    )
    def test_habit_create_invalid_lead_time_validators(self, invalid_value, expected_error) -> None:
        """Тест обновления привычки с невалидным полем 'lead_time'(проверка кастомным валидатором)"""

        url = reverse("habits:habits-list")
        invalid_data = {
            "user": self.user.email,
            "is_pleasant": False,
            "action": "полезное действие",
            "reward_habit": self.reward_habit.pk,
            "frequency_days": 1,
            "time": time(12, 0),
            "lead_time": invalid_value,
        }
        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertEqual(response.data["non_field_errors"][0], expected_error)

    @parameterized.expand(
        [
            ("16-00", "Введите время выполнения в формате ЧЧ:ММ:СС или ММ:СС (максимум 2 минуты)!"),
            (None, "Это поле не может быть пустым (null)!"),
        ]
    )
    def test_habit_update_invalid_lead_time_serializers(self, invalid_value, expected_error) -> None:
        """Тест обновления привычки с невалидным полем 'lead_time'(проверка в сериализаторе)"""

        url = reverse("habits:habits-detail", args=(self.habit.pk,))
        invalid_data = {
            "lead_time": invalid_value,
        }
        response = self.client.patch(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lead_time", response.data)
        self.assertEqual(response.data["lead_time"][0], expected_error)

    @parameterized.expand(
        [
            (timedelta(minutes=12), "'lead_time': Время выполнения не должно превышать 2 минуты!"),
            ("", "'lead_time': Время выполнения не должно быть нулевое или отрицательное!"),
        ]
    )
    def test_habit_update_invalid_lead_time_validators(self, invalid_value, expected_error) -> None:
        """Тест обновления привычки с невалидным полем 'lead_time'(проверка кастомным валидатором)"""

        url = reverse("habits:habits-detail", args=(self.habit.pk,))
        invalid_data = {
            "lead_time": invalid_value,
        }
        response = self.client.patch(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertEqual(response.data["non_field_errors"][0], expected_error)

    @parameterized.expand(
        [
            ("", "Формат времени должен быть HH:MM:SS (например, '14:30:00')!"),
            (None, "Это поле не может быть пустым (null)!"),
        ]
    )
    def test_habit_create_invalid_time_serializers(self, invalid_value, expected_error) -> None:
        """Тест обновления привычки с невалидным полем 'lead_time'(проверка в сериализаторе)"""

        url = reverse("habits:habits-list")
        invalid_data = {
            "user": self.user.email,
            "action": "полезное действие",
            "reward_habit": self.reward_habit.pk,
            "frequency_days": 1,
            "time": invalid_value,
            "lead_time": timedelta(minutes=2),
        }
        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("time", response.data)
        self.assertEqual(response.data["time"][0], expected_error)

    def test_habit_create_not_field_action(self) -> None:
        """Тест обновления привычки с невалидным полем 'lead_time'(проверка в сериализаторе)"""

        url = reverse("habits:habits-list")
        invalid_data = {
            "user": self.user.email,
            "reward_habit": self.reward_habit.pk,
            "frequency_days": 1,
            "time": time(12, 0),
            "lead_time": timedelta(minutes=2),
        }
        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("action", response.data)
        self.assertEqual(response.data["action"][0], "Это поле обязательно для заполнения!")

    def test_habit_create_invalid_action(self) -> None:
        """Тест обновления привычки с невалидным полем 'lead_time'(проверка в сериализаторе)"""

        url = reverse("habits:habits-list")
        invalid_data = {
            "user": self.user.email,
            "action": None,
            "reward_habit": self.reward_habit.pk,
            "frequency_days": 1,
            "time": time(12, 0),
            "lead_time": timedelta(minutes=2),
        }
        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("action", response.data)
        self.assertEqual(response.data["action"][0], "Данное поле не может иметь значение null!")


class HabitReminderTest(APITestCase):
    """Тест кейс для проверки установки расписания напоминаний"""

    def setUp(self):
        """Инициализация тестовых данных"""

        self.user = User.objects.create(email="testuser@example.com")
        self.habit = Habit.objects.create(
            user=self.user,
            action="Test habit",
            frequency_days=1,
            lead_time=timedelta(minutes=2),
            time=time(18, 10),
        )
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        """Удаление всех связанных задач (на случай, если тест упал на середине)"""
        PeriodicTask.objects.filter(name__contains=f"Habit-{self.habit.pk}").delete()

    def test_reminder_creation(self):
        """Тест создания расписания для привычки"""

        setup_habit_reminder(self.habit)

        task = PeriodicTask.objects.filter(name=f"Habit Reminder {self.habit.pk} - {self.habit.action[:50]}").first()

        self.assertTrue(task, "Периодическая задача не была создана")
        self.assertEqual(task.task, "habits.tasks.send_reminder")
        self.assertEqual(task.name, f"Habit Reminder {self.habit.pk} - {self.habit.action[:50]}")


class TelegramMessageTest(APITestCase):
    """Тест кейс для проверки отправки сообщения пользователю в телеграм-чат"""

    @patch("requests.get")
    def test_send_message_success(self, mock_get):
        """Тест отправки сообщения в телеграм-чат"""

        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}

        test_chat_id = "123456789"
        test_message = "Test message"

        result = send_telegram_message(test_chat_id, test_message)

        self.assertTrue(result)

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn(settings.TELEGRAM_BOT_TOKEN, args[0])
        self.assertEqual(kwargs["params"]["chat_id"], test_chat_id)
        self.assertEqual(kwargs["params"]["text"], test_message)

    def test_send_message_output(self):
        """Тест с перехватом вывода в консоль"""

        with patch("sys.stdout", new_callable=StringIO) as fake_out:
            send_telegram_message("123456789", "Test message")
            output = fake_out.getvalue()

            assert "Отправка сообщения 'Test message' для chat_id 123456789" in output


class SendInformationTaskTest(APITestCase):
    """Тест кейс для проверки выполнения задачи по отправке сообщения"""

    def setUp(self):
        """Инициализация тестовых данных"""

        self.user = User.objects.create(email="test@example.com", tg_chat_id="123456789")
        self.habit = Habit.objects.create(
            user=self.user,
            action="Test habit",
            frequency_days=1,
            lead_time=timedelta(minutes=2),
            time=time(18, 10),
        )
        self.client.force_authenticate(user=self.user)

    @patch("habits.tasks.send_telegram_message")
    @patch("habits.tasks.send_mail")
    def test_send_information_success(self, mock_send_mail, mock_send_telegram):
        """Тест успешной отправки информации"""

        send_information(self.user.email)

        mock_send_telegram.assert_called_once_with(
            self.user.tg_chat_id, f"Вы создали привычку: {self.habit.pk} - {self.habit.action}"
        )
        mock_send_mail.assert_called_once()

    @patch("habits.tasks.send_telegram_message")
    def test_user_not_found(self, mock_send_telegram):
        """Тест случая, когда пользователь не найден"""

        with patch("builtins.print") as mock_print:
            send_information("nonexistent@example.com")
            mock_print.assert_called_with("Пользователь с email 'nonexistent@example.com' не найден")

        mock_send_telegram.assert_not_called()


class SendReminderTaskTest(APITestCase):
    """Тест кейс для проверки отправки напоминаний по расписанию"""

    def setUp(self):
        """Инициализация тестовых данных"""

        self.user = User.objects.create(email="test@example.com", tg_chat_id="123456789")
        self.habit = Habit.objects.create(
            user=self.user,
            action="Test habit",
            frequency_days=1,
            lead_time=timedelta(minutes=2),
            time=time(12, 0),
        )
        self.client.force_authenticate(user=self.user)
        self.now = timezone.localtime()

    def tearDown(self):
        """Очистка данных в кэше"""
        cache.clear()

    @patch("habits.tasks.timezone.localtime")
    @patch("habits.tasks.send_telegram_message")
    @patch("habits.tasks.send_reminder.update_state")
    def test_reminder_at_correct_time(self, mock_update, mock_send_telegram, mock_localtime):
        """Тест отправки в правильное время"""

        mock_now = datetime.combine(self.now.date(), time(11, 59)).replace(tzinfo=timezone.get_current_timezone())

        mock_localtime.return_value = mock_now
        mock_send_telegram.return_value = True

        result = send_reminder(habit_id=self.habit.pk)

        mock_send_telegram.assert_called_once_with(
            "123456789", "Напоминание о привычке!\nДействие: Test habit\nВремя выполнения: 12:00\nМесто: не указано"
        )

        mock_update.assert_called_once_with(
            state="PROGRESS", meta={"current": self.habit.pk, "status": "telegram sent"}
        )

        self.assertIn("Успешно отправлено", result)
