from datetime import time
from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from habits.models import Habit


class FrequencyValidator:
    """Класс-валидатор для проверки, что привычка будет выпоkняться не реже,
    чем 1 раз в 7 дней"""

    def __init__(self, field: str) -> None:
        """Инициализирует валидатор с указанием имени поля для проверки"""
        self.field = field

    def __call__(self, value: dict) -> None:
        """Выполняет проверку поля с периодичностью"""

        search_field = value.get(self.field)
        print(f"Получено значение {self.field}, {value}, {search_field}")

        if search_field is None:
            raise serializers.ValidationError(
                "Поле 'frequency_days' обязательно для заполнения"
            )

        if search_field and search_field > 7:
            raise serializers.ValidationError("'frequency_days': Максимальная периодичность - 1 раз в 7 дней")
        if search_field and search_field < 1:
            raise serializers.ValidationError("'frequency_days': Минимальная периодичность - 1 раз в день")


class RewardHabitValidator:
    """Валидация для полей 'is_pleasant', 'reward' и 'reward_habit'"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Класс-валидатор работает с фиксированными полями"""
        pass

    def __call__(self, data: dict[str, str]) -> None:
        """Выполняет проверку полей 'is_pleasant', 'reward', 'reward_habit'"""

        self.instance = getattr(self, "instance", None)

        is_pleasant = data.get("is_pleasant", getattr(self.instance, "is_pleasant", False))
        reward = data.get("reward", getattr(self.instance, "reward", None))
        reward_habit = data.get("reward_habit", getattr(self.instance, "reward_habit", None))

        if is_pleasant is None and self.instance:
            is_pleasant = self.instance.is_pleasant
        is_pleasant = is_pleasant or False

        if reward_habit:
            if not isinstance(reward_habit, Habit):
                try:
                    reward_habit = Habit.objects.get(pk=reward_habit)
                except Habit.DoesNotExist:
                    raise serializers.ValidationError("")
                except ValueError:
                    raise serializers.ValidationError({
                        "reward_habit": ["Некорректный ID привычки"]
                    })



        data['reward_habit'] = reward_habit.pk

        if is_pleasant:
            if reward_habit and reward:
                raise serializers.ValidationError({
                    "reward_habit": "Приятная привычка не может иметь связанную привычку!",
                    "reward": "Приятная привычка не может иметь вознаграждение!"
                })
            if reward_habit:
                raise serializers.ValidationError("'reward_habit': Приятная привычка не может иметь связанную привычку!")
            if self.instance and self.instance.reward_habit and reward_habit is None:
                raise serializers.ValidationError("Приятная привычка не должная содержать связанную привычку!")

            if reward:
                raise serializers.ValidationError("'reward': Приятная привычка не может иметь вознаграждение!")
            if self.instance and self.instance.reward_habit and reward_habit is None:
                raise serializers.ValidationError("Приятная привычка не должная содержать вознаграждение!")

        else:
            if not reward_habit.is_pleasant:
                raise serializers.ValidationError({
                    "reward_habit": ["В качестве связанной привычки можно указывать только приятную!"]
                })
            if reward and reward_habit:
                raise serializers.ValidationError("'reward', 'reward_habit': Выберите что-то одно: приятную привычку или вознаграждение")


class LeadTimeValidator:
    """Валидация для поля 'lead_time'"""

    def __init__(self, field: str) -> None:
        """Инициализирует валидатор с указанием имени поля для проверки"""
        self.field = field

    def __call__(self, value: dict) -> None:
        """Проверяет, что время на выполнение привычки не превышает 2 минуты'"""

        lead_time = dict(value).get(self.field)

        if lead_time is None:
            return

        if lead_time and lead_time > time(hour=0, minute=2):
            raise ValidationError(
                "'lead_time': Время выполнения не должно превышать 2 минуты!"
            )
