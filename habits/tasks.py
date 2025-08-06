import os
from datetime import datetime

from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

from config import settings
from habits.models import Habit
from habits.services import send_telegram_message
from users.models import User


@shared_task
def send_information(email):
    """Отправляет сообщение пользователю о создании привычки"""

    try:
        user = User.objects.get(email=email)

        latest_habit = Habit.objects.filter(user=user).order_by("-created_at").first()
        print(f"Последняя привычка: {latest_habit}")

        if not latest_habit:
            print(f"У пользователя {email} нет привычек")
            return

        message = f"Вы создали привычку: {latest_habit.pk} - {latest_habit.action}"

        if user.tg_chat_id:
            print(f"Телеграм-чат id: {user.tg_chat_id}")

            send_telegram_message(user.tg_chat_id, message)
            print(
                f"Создана привычка: {latest_habit.action}, отправлено сообщение в Телеграм пользователю {latest_habit.user.tg_chat_id}"
            )
            if user.email:
                send_mail(
                    subject="Информация о создании привычки",
                    message=f"Создана привычка - {latest_habit}",
                    from_email=os.getenv("EMAIL_HOST_USER"),
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                print(
                    f"Создана привычка: {latest_habit.action}, отправлено на почту сообщение пользователю {latest_habit.user.email}"
                )
    except User.DoesNotExist:
        print(f"Пользователь с email '{email}' не найден")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


@shared_task(bind=True)
def send_reminder(self, habit_id=None):
    """Отправляет пользователю сообщение-напоминание о выполнении привычки"""

    try:
        now = timezone.localtime()
        print(f"=== Запуск отправки в {now} ===")

        lock_id = f"habit_reminder_lock_{habit_id or 'all'}"
        if not cache.add(lock_id, True, timeout=300):
            print("Задача уже выполняется, пропускаем")
            return

        if habit_id:
            habits = Habit.objects.filter(id=habit_id, is_pleasant=False, time__isnull=False)
        else:
            # Иначе выбираем все подходящие привычки
            habits = Habit.objects.filter(is_pleasant=False, time__isnull=False).select_related("user")

        if not habits.exists():
            print("Нет привычек для напоминания")
            return "Нет привычек для напоминания"

        success_count_tg = 0
        # success_count_email = 0

        for habit in habits:
            print(f"Проверка пользователя {habit.user}:")
            print(f"TG Chat ID: {habit.user.tg_chat_id}")
            print(f"Telegram Bot Token: {settings.TELEGRAM_BOT_TOKEN[:5]}...")
            try:
                habit_time = timezone.make_aware(datetime.combine(now.date(), habit.time))

                # Проверяем разницу во времени (в минутах)
                time_diff = (habit_time - now).total_seconds() / 60

                print(f"Habit time: {habit_time}, Diff: {time_diff:.1f} min")

                if 0 <= time_diff <= 2:
                    print(f"Time difference: {time_diff} minutes")
                    print(f"Habit time: {habit.time}")
                    message = (
                        f"Напоминание о привычке!\n"
                        f"Действие: {habit.action}\n"
                        f"Время выполнения: {habit.time.strftime('%H:%M')}\n"
                        f"Место: {habit.location or 'не указано'}"
                    )

                    if habit.user.tg_chat_id:
                        send_telegram_message(habit.user.tg_chat_id, message)
                        self.update_state(state="PROGRESS", meta={"current": habit.pk, "status": "telegram sent"})
                        print(f"Отправлено сообщение в Телеграм пользователю {habit.user.tg_chat_id}")
                        success_count_tg += 1

                    # if habit.user.email:
                    #     send_mail(
                    #         subject=f"Напоминание: {habit.action}",
                    #         message=message,
                    #         from_email=settings.DEFAULT_FROM_EMAIL,
                    #         recipient_list=[habit.user.email],
                    #         fail_silently=False
                    #     )
                    #     print(
                    #         f"Отправлено напоминание о выполнении привычки: {habit.action}, на почту пользователя: {habit.user.email}")
                    #     success_count_email += 1
                else:
                    continue

            except Exception as e:
                print(f"Ошибка при обработке привычки {habit.pk}: {str(e)}")
                continue
            finally:
                cache.delete(lock_id)

            # print(f"Успешно отправлено {success_count_tg} напоминаний в телеграм, {success_count_email} напоминаний на email")
            print(f"Успешно отправлено {success_count_tg} напоминаний в телеграм")
            # return f"Успешно отправлено {success_count_tg} напоминаний в телеграм, {success_count_email} напоминаний на email"
            return f"Успешно отправлено {success_count_tg} напоминаний в телеграм"

    except Exception as e:
        error_msg = f"Критическая ошибка: {str(e)}"
        print(error_msg)
        self.retry(exc=e, countdown=600)
