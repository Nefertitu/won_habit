from typing import Optional

from rest_framework import serializers

from habits.models import Habit


class HabitSerializer(serializers.ModelSerializer):
    """Сериализатор для модели 'Habit'"""

    user = serializers.SerializerMethodField()

    def get_user(self, instance: Habit) -> Optional[str]:
        """Возвращает email пользователя-создателя привычки"""
        return str(instance.user.email) if instance.user else None

    class Meta:
        model = Habit
        fields = "__all__"