from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from config import settings


class Habit(models.Model):
    """Модель Привычка"""

    DAILY = "Ежедневно"
    EVERY_2_DAYS = "Каждые 2 дня"
    EVERY_3_DAYS = "Каждые 3 дня"
    EVERY_4_DAYS = "Каждые 4 дня"
    EVERY_5_DAYS = "Каждые 5 дней"
    EVERY_6_DAYS = "Каждые 6 дней"
    WEEKLY = "Еженедельно"

    FREQUENCY_CHOICES = [
        (DAILY, "Ежедневно"),
        (EVERY_2_DAYS, "Каждые 2 дня"),
        (EVERY_3_DAYS, "Каждые 3 дня"),
        (EVERY_4_DAYS, "Каждые 4 дня"),
        (EVERY_5_DAYS, "Каждые 5 дней"),
        (EVERY_6_DAYS, "Каждые 6 дней"),
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
    frequency_days = models.PositiveSmallIntegerField(
        verbose_name="Периодичность в днях в неделю",
        help_text="Интервал выполнения (1-7 дней)",
        default=1,
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
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания привычки",
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата и время обновления привычки",
        auto_now=True,
    )

    def __str__(self) -> str:
        """Строковое отображение модели Привычка"""
        if self.is_pleasant:
            return f"Приятная привычка: Я буду {self.action}"
        return f"Полезная привычка: Я буду {self.action} в {self.time} {self.location}"

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        constraints = [
            models.CheckConstraint(
                check=models.Q(frequency_days__gte=1) & models.Q(frequency_days__lte=7),
                name="check_frequency_range"
            )
        ]


