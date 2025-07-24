from django.db import models

from config import settings


class Habit(models.Model):
    """Модель Привычка"""

    DAILY = "Ежедневно"
    WEEKLY = "Еженедельно"

    FREQUENCY_CHOICES = [
        (DAILY, "Ежедневно"),
        (WEEKLY, "Еженедельно"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        verbose_name="Пользователь",
        related_name="user_habits",
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Место",
        help_text="Укажите место, в котором необходимо выполнять привычку",
    )
    time = models.TimeField(
        verbose_name="Время",
        blank=True,
        null=True,
        help_text="Укажите время, когда необходимо выполнять привычку",
    )
    action = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Действие",
        help_text="Укажите действие, которое представляет собой привычка",
    )
    is_pleasant = models.BooleanField(
        default=False,
        verbose_name="Приятная привычка",
        help_text="Привычка, которую можно привязать к выполнению полезной привычки",
    )
    reward_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"is_pleasant": True},
        verbose_name="Привычка-вознаграждение",
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        verbose_name="Периодичность",
        help_text="Установите периодичность выполнения",
        default=DAILY,
    )
    reward = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Вознаграждение",
    )
    lead_time = models.TimeField(
        verbose_name="Время на выполнение",
        blank=True,
        null=True,
        help_text="Укажите время, достаточное для выполнения привычки",
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Публичная привычка",
        help_text="Активировать, если привычку можно публиковать в общий доступ",
    )

    def __str__(self) -> str:
        """Строковое отображение модели Привычка"""
        if self.is_pleasant:
            return f"Приятная привычка {self.reward_habit}"
        return f"Полезная привычка {self.action}"

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"


