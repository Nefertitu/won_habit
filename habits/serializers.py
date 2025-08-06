from typing import Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from habits.models import Habit
from habits.validators import FrequencyValidator, RewardHabitValidator, LeadTimeValidator, RequiredFieldTimeValidator

class HabitSerializer(serializers.ModelSerializer):
    """Сериализатор для модели 'Habit'"""

    user = serializers.SerializerMethodField()
    frequency_days = serializers.IntegerField(
        min_value=1,
        max_value=7,
        required=False,
        allow_null=False,
        error_messages={
            "invalid": "'frequency_days' должно быть числом от 1 до 7!",
            "min_value": "'frequency_days' не может быть меньше 1!",
            "max_value": "'frequency_days' не может быть больше 7!",
            "null": "Данное поле не может иметь значение null!"
        }
    )
    reward_habit = serializers.PrimaryKeyRelatedField(
        queryset=Habit.objects.all(),
        required=False,
        allow_null=True,
        error_messages = {
            "does_not_exist": "Недопустимый pk '{pk_value}' - привычка с таким pk не существует!",
            "incorrect_type": "Неверный тип. Ожидалось значение pk, получено {data_type}!"
        }
    )
    action = serializers.CharField(
        required=True,
        error_messages={
            "required": "Это поле обязательно для заполнения!",
            "null": "Данное поле не может иметь значение null!"
        }
    )
    time = serializers.TimeField(
        required=False,
        format="%H:%M:%S",
        error_messages={
            "invalid": "Формат времени должен быть HH:MM:SS (например, '14:30:00')!",
            "null": "Это поле не может быть пустым (null)!",
            # "required": "Это поле обязательно для заполнения!"

        }
    )
    lead_time = serializers.DurationField(
        required=False,
        error_messages={
            "invalid": "Введите время выполнения в формате ЧЧ:ММ:СС или ММ:СС (максимум 2 минуты)!",
            "null": "Это поле не может быть пустым (null)!"
        }
    )

    def get_user(self, instance: Habit) -> Optional[str]:
        """Возвращает email пользователя-создателя привычки"""
        return str(instance.user.email) if instance.user else None


    class Meta:
        model = Habit
        fields = "__all__"
        # extra_kwargs = {
        #     'time': {
        #         'error_messages': {
        #             'invalid': "Формат времени должен быть HH:MM:SS (например, '14:30:00')!",
        #             # 'required': "Поле обязательно для заполнения",
        #             "null": "Данное поле не может иметь значение null!"
        #         }
        #     },
        #     'lead_time': {
        #         'error_messages': {
        #             'invalid': "Введите время выполнения в формате ЧЧ:ММ:СС или ММ:СС (максимум 2 минуты)!",
        #             # 'required': "Поле обязательно"
        #         }
        #     },
            # 'frequency_days': {
            #     'error_messages': {
            #         # 'invalid': "Введите время выполнения в формате ЧЧ:ММ:СС или ММ:СС (максимум 2 минуты)!",
            #         # 'required': "Поле обязательно",
            #         "null": "Данное поле не может иметь значение null!"
            #     }
            # },
        # }

        validators = [FrequencyValidator(), RewardHabitValidator(), LeadTimeValidator(), RequiredFieldTimeValidator()]

