from datetime import datetime, time, timedelta
from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from habits.models import Habit


class FrequencyValidator:
    """Класс-валидатор для проверки поля 'frequency_days'"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Класс-валидатор работает с фиксированными полями"""
        pass

    def __call__(self, data: dict) -> None:
        """
        Проверяет:
        1. Обязательность поля для полезных привычек
        2. Периодичность выполнения не может быть меньше 1 и больше 7 раз в неделю
        """

        self.instance = getattr(self, "instance", None)
        self.partial_update = getattr(self, "partial", True)

        is_pleasant = data.get("is_pleasant", getattr(self.instance, "is_pleasant", False))
        # frequency_days = data.get("frequency_days", getattr(self.instance, "frequency_days", False))
        frequency_days = data.get("frequency_days")

        if not is_pleasant:
            if not self.instance and not self.partial_update:
                if not frequency_days:
                    raise serializers.ValidationError("'frequency_days': Для полезных привычек это обязательное поле!")
                if "frequency_days" in data and data["frequency_days"] is None:
                    raise serializers.ValidationError("'frequency_days': Данное поле не может иметь значение null!")

            if self.partial_update:
                if "frequency_days" in data and data["frequency_days"] is None:
                    raise serializers.ValidationError("'frequency_days': Данное поле не может иметь значение null!")
        if frequency_days is not None:
            if frequency_days < 1 or frequency_days > 7:
                raise ValidationError("Периодичность должна быть 1-7 дней")


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

        if reward_habit and not isinstance(reward_habit, Habit):
            try:
                reward_habit = Habit.objects.get(pk=reward_habit)
            except ValueError:
                raise serializers.ValidationError({"reward_habit": ["Некорректный ID привычки"]})

        if is_pleasant:
            if reward_habit:
                raise serializers.ValidationError(
                    "'reward_habit': Приятная привычка не может иметь связанную привычку!"
                )

            if reward:
                raise serializers.ValidationError("'reward': Приятная привычка не может иметь вознаграждение!")

        else:
            if reward_habit is not None:
                if not reward_habit.is_pleasant:
                    raise serializers.ValidationError(
                        {"reward_habit": ["В качестве связанной привычки можно указывать только приятную!"]}
                    )
                if reward and reward_habit:
                    raise serializers.ValidationError(
                        "'reward', 'reward_habit': Выберите что-то одно: приятную привычку или вознаграждение"
                    )


class LeadTimeValidator:
    """Валидация для поля 'lead_time'"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Класс-валидатор работает с фиксированными полями"""
        pass

    def __call__(self, data: dict) -> None:
        """
        Проверяет:
        1. Обязательность поля для полезных привычек
        2. Максимальное время выполнения (2 минуты)
        """

        self.instance = getattr(self, "instance", None)
        self.partial_update = getattr(self, "partial", True)

        is_pleasant = data.get("is_pleasant", getattr(self.instance, "is_pleasant", False))
        # lead_time = data.get("lead_time", getattr(self.instance, "lead_time", None))
        lead_time = data.get("lead_time")

        if not is_pleasant:
            if not self.instance and not self.partial_update:
                if not lead_time:
                    raise serializers.ValidationError("'lead_time': Для полезных привычек это обязательное поле!")

                if "lead_time" not in data and not self.instance and not self.partial_update:
                    raise serializers.ValidationError(
                        "'lead_time': Для полезной привычки это поле обязательно для заполнения!"
                    )

            # if not self.partial_update and "lead_time" not in data:
            #     raise serializers.ValidationError(
            #         "'lead_time': Для полезной привычки это поле обязательно для заполнения!"
            #     )
            if self.instance and self.partial_update:
                if "lead_time" in data and data["lead_time"] is None:
                    raise serializers.ValidationError("'lead_time': Данное поле не может иметь значение null!")
                # if not lead_time:
                #     raise serializers.ValidationError("'lead_time': Для полезных привычек это обязательное поле!")

        if "lead_time" in data and data["lead_time"] is not None:
            if lead_time <= timedelta(minutes=0):
                raise ValidationError("'lead_time': Время выполнения не должно быть нулевое или отрицательное!")
            if lead_time > timedelta(minutes=2):
                raise ValidationError("'lead_time': Время выполнения не должно превышать 2 минуты!")


class RequiredFieldTimeValidator:
    """Валидация обязательного для полезной привычки поля 'time'"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Класс-валидатор работает с фиксированными полями"""
        pass

    def __call__(self, data: dict) -> None:
        """Выполняет проверку поля 'time'"""

        self.instance = getattr(self, "instance", None)
        self.partial_update = getattr(self, "partial", True)
        # time_value = data.get("time", getattr(self.instance, "time", None))
        time_value = data.get("time")

        is_pleasant = data.get("is_pleasant", getattr(self.instance, "is_pleasant", False))

        if not is_pleasant:
            if not self.instance and not self.partial_update:
                if not time_value:
                    raise serializers.ValidationError("'time': Для полезных привычек это обязательное поле!")
                if "time" in data and data["time"] is None:
                    raise serializers.ValidationError("'time': Данное поле не может иметь значение null!")
            if self.instance and self.partial_update:
                if "lead_time" in data and data["lead_time"] is None:
                    raise serializers.ValidationError("'lead_time': Данное поле не может иметь значение null!")

            # if time_value and time_value != datetime.strptime(time_value, "%H:%M:%S").time():
            #     raise serializers.ValidationError(
            #         "'time': Введите время выполнения в формате ЧЧ:ММ:СС или секундах (максимум 2 минуты)!"
            #     )
