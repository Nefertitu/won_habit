import json
from datetime import datetime, timedelta

import requests
from django.utils import timezone

from django_celery_beat.models import IntervalSchedule, PeriodicTask

from config import settings



def setup_habit_reminder(habit):
    """Устанавливает интервал напоминания"""

    print(f"Установлено напоминание для привычки: {habit.id}")
    print(f"Пользователь: {habit.user}, TG Chat ID: {getattr(habit.user, 'tg_chat_id', None)}")
    print(f"Время напоминания: {habit.time}, периодичность: {habit.frequency_days} дней в неделю")
    try:
        if not habit.time or not habit.frequency_days:
            print(f"Привычка {habit.id} не имеет времени или периодичности")
            return

        frequency = habit.frequency_days

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=frequency,
            period=IntervalSchedule.DAYS,
        )

        task_name = f"Habit Reminder {habit.id} - {habit.action[:50]}"
        now = timezone.localtime()
        # print(f"Now: {now}")
        reminder_time_naive = datetime.combine(now.date(), habit.time)
        # print(f"Remainder_time_naive: {reminder_time_naive}")
        reminder_time = timezone.make_aware(reminder_time_naive)
        # print(f"Reminder_time: {reminder_time}")

        if reminder_time < now:
            reminder_time += timedelta(days=1)
            print(f"Переносим напоминание на: {reminder_time}")

        if settings.DEBUG:
            test_time = now + timedelta(minutes=2)
            print(f"ТЕСТОВЫЙ РЕЖИМ: напоминание в {test_time}")
            reminder_time = test_time

        if PeriodicTask.objects.filter(name=f"Habit-{habit.id}-Reminder").exists():
            return
        task = PeriodicTask.objects.create(
            interval=schedule,
            name=task_name,
            task=f"habits.tasks.send_reminder",
            args=json.dumps([habit.id]),
            start_time=reminder_time,
            description=f"Reminder for {habit.action}",
            enabled=True,

        )
        print(f"Напоминание настроено: {task}")
    except Exception as e:
        print(f"Ошибка настройки напоминания: {e}")
        raise


def send_telegram_message(chat_id, message):
    """"""

    print(f"Attempting to send Telegram message to chat {chat_id}")
    try:
        params = {
            "text": message,
            "chat_id": chat_id,
        }
        response = requests.get(f"{settings.TELEGRAM_URL}{settings.TELEGRAM_BOT_TOKEN}/sendMessage", params=params)
        print(f"Отправка сообщения '{message}' для chat_id {chat_id}")

        if response.status_code == 200:
            return True
        else:
            print(f"Ошибка Telegram API: {response.json()}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке сообщения в Telegram: {e}")
        return False
