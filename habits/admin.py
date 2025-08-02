from django.contrib import admin

from habits.models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    """Администрирование привычек. Позволяет управлять
    привычками, с возможностью фильтрации и поиска."""

    list_display = (
    "id",
    "user",
    "action",
    "is_pleasant",
    "frequency_days",
    )

    list_filter = ("id",)
    search_fields = ("action","reward_habit")
