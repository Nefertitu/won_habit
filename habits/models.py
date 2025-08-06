from datetime import timedelta, time

from django.db import models

from config import settings


class Habit(models.Model):
    """Модель Привычка"""

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
        default=time(12, 0),
        help_text="Укажите время, когда необходимо выполнять привычку",
    )
    action = models.CharField(
        max_length=200,
        blank=False,
        null=False,
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
        help_text="Укажите интервал выполнения (1-7 дней)",
        blank=True,
        null=True,
        default=1,
    )
    reward = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Вознаграждение",
    )
    lead_time = models.DurationField(
        verbose_name="Время на выполнение",
        blank=True,
        null=True,
        default=timedelta(minutes=2),
        help_text="Укажите время, достаточное для выполнения привычки (максимум 2 минуты)",
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
            return f"Приятная привычка: {self.action}"
        return f"Полезная привычка: {self.action}, время выполнения: {self.time}, периодичность: {self.frequency_days} дней в неделю"

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        constraints = [
            models.CheckConstraint(
                check=models.Q(frequency_days__gte=1) &
                      models.Q(frequency_days__lte=7),
                name="check_frequency_range",
                violation_error_message="Периодичность может быть от 1 до 7 дней в неделю!"
            ),
            models.CheckConstraint(
                check=models.Q(is_pleasant=True) |
                models.Q(frequency_days__isnull=False),
                name="frequency_required_for_useful",
                violation_error_message="Для полезной привычки поле 'Периодичность' обязательно для заполнения!"
            ),
            models.CheckConstraint(
                check=models.Q(lead_time__isnull=True) |
                      models.Q(lead_time__lte=timedelta(minutes=2)),
                name="max_lead_time_2min",
                violation_error_message="Время выполнения не должно превышать 2 минуты!"
            ),
            models.CheckConstraint(
                check=models.Q(is_pleasant=True) |
                models.Q(lead_time__isnull=False),
                name="lead_time_required_for_useful",
                violation_error_message="Для полезной привычки поле 'Время на выполнение' обязательно для заполнения"
            ),
            models.CheckConstraint(
                check=models.Q(is_pleasant=False) |
                      models.Q(is_pleasant=True) &
                      models.Q(reward_habit__isnull=True),
                name="pleasant_habit_no_reward_habit",
                violation_error_message="У приятной привычки не может быть связанной привычки"
            ),
            models.CheckConstraint(
                check=models.Q(is_pleasant=False) |
                      models.Q(is_pleasant=True) &
                      models.Q(reward__isnull=True),
                name="pleasant_habit_no_reward",
                violation_error_message="У приятной привычки не может быть вознаграждения"
            ),
            models.CheckConstraint(
                check=models.Q(is_pleasant=True) |
                      (models.Q(is_pleasant=False) &
                      models.Q(reward_habit__isnull=False) &
                      models.Q(reward__isnull=True) |
                      models.Q(reward_habit__isnull=True) &
                      models.Q(reward__isnull=False) |
                      models.Q(reward__isnull=True) &
                      models.Q(reward_habit__isnull=True)
                       ),
                name="useful_habit_reward_logic",
                violation_error_message="У полезной привычки может быть либо связанная приятная привычка, либо вознаграждение!"
            ),
            models.CheckConstraint(
                check=models.Q(is_pleasant=True) |
                models.Q(time__isnull=False),
                name="time_required_for_useful",
                violation_error_message="Для полезной привычки поле 'Время' обязательно для заполнения"
            ),
        ]
