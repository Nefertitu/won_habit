from datetime import time
from typing import Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from habits.models import Habit


class HabitSerializer(serializers.ModelSerializer):
    """Сериализатор для модели 'Habit'"""

    user = serializers.SerializerMethodField()

    def get_user(self, instance: Habit) -> Optional[str]:
        """Возвращает email пользователя-создателя привычки"""
        return str(instance.user.email) if instance.user else None

    def validate(self, data):
        """"""

        is_pleasant = data.get("is_pleasant", getattr(self.instance, 'is_pleasant', False))
        reward = data.get("reward", getattr(self.instance, "reward", None))
        reward_habit = data.get("reward_habit", getattr(self.instance, "reward_habit", None))

        if reward_habit:
            if isinstance(reward_habit, Habit):
                try:
                    reward_habit = Habit.objects.get(pk=reward_habit)
                    data["reward_habit"] = reward_habit
                except Habit.DoesNotExist:
                    raise serializers.ValidationError("Привычка-вознаграждение не найдена!")
                if not reward_habit.is_pleasant:
                    raise serializers.ValidationError("Связанная привычка должна быть приятной!")
                if reward_habit.reward_habit:
                    raise serializers.ValidationError("Приятная привычка не может иметь другую связанную приятную привычку!")
                if reward_habit.reward:
                    raise serializers.ValidationError("Приятная привычка не может иметь вознаграждение!")

        if is_pleasant and reward and reward_habit:
            raise serializers.ValidationError("Выберите что-то одно: приятную привычку или вознаграждение!")

        if reward_habit and not is_pleasant:
            raise serializers.ValidationError("Связанная привычка должна быть приятной!")

        lead_time = data.get("lead_time", getattr(self.instance, "lead_time", None))
        if lead_time and lead_time > time(hour=0, minute=2):
            raise serializers.ValidationError("Время выполнения не должно превышать 2 минуты!")

        return data

    class Meta:
        model = Habit
        fields = "__all__"