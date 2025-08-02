from typing import Optional

from rest_framework import serializers

from habits.models import Habit
from habits.validators import FrequencyValidator, RewardHabitValidator, LeadTimeValidator


class HabitSerializer(serializers.ModelSerializer):
    """Сериализатор для модели 'Habit'"""

    user = serializers.SerializerMethodField()
    frequency_days = serializers.IntegerField(
        min_value=1,
        max_value=7,
        error_messages={
            "invalid": "'frequency_days' должно быть числом от 1 до 7",
            "min_value": "'frequency_days' не может быть меньше 1",
            "max_value": "'frequency_days' не может быть больше 7"
        }
    )
    reward_habit = serializers.PrimaryKeyRelatedField(
        queryset=Habit.objects.all(),
        required=False,
        allow_null=True,
        error_messages = {
            'required': "Это поле обязательно для заполнения",
            'does_not_exist': "Недопустимый pk '{pk_value}' - привычка с таким pk не существует",
            'incorrect_type': "Неверный тип. Ожидалось значение pk, получено {data_type}",
        }
    )


    def get_user(self, instance: Habit) -> Optional[str]:
        """Возвращает email пользователя-создателя привычки"""
        return str(instance.user.email) if instance.user else None


    class Meta:
        model = Habit
        validators = [FrequencyValidator(field="frequency_days"), RewardHabitValidator(), LeadTimeValidator(field="lead_time")]
        fields = "__all__"
