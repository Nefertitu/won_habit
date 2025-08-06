from typing import Union, Sequence, Any

from django.db.models import QuerySet
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, BasePermission, OperandHolder, SingleOperandHolder
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from habits.models import Habit
from habits.paginators import HabitsPaginator
from habits.serializers import HabitSerializer
from habits.services import setup_habit_reminder
from habits.tasks import send_information
from users.permissions import IsOwnerOnly


class HabitViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с курсами"""

    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = HabitsPaginator

    PermissionClass = Union[type[BasePermission], OperandHolder, SingleOperandHolder]

    def get_queryset(self) -> QuerySet[Habit] | None:
        """Фильтрует привычки в зависимости от прав пользователя"""
        user = self.request.user

        if not user.is_authenticated:
            return Habit.objects.none()
        return Habit.objects.filter(user=user)

    def get_permissions(self) -> Sequence[Any]:
        """
        Управление разрешениями:
        (GET /habits/        # Список
        GET /habits/{id}/    # Просмотр
        PUT /habits/{id}/    # Полное обновление (только пользователь-создатель)
        PATCH /habits/{id}/  # Частичное обновление (только пользователь-создатель)
        DELETE /habits/{id}/ # Удаление (только пользователь-создатель)
        )
        """

        if self.action == "create":
            self.permission_classes = [IsAuthenticated]
        elif self.action in ["update", "retrieve", "destroy", "list"]:
            self.permission_classes = [IsAuthenticated, IsOwnerOnly]
        return super().get_permissions()


    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Создает объект 'Habit' и автоматически назначает пользователя"""

        habit = serializer.save(user=self.request.user)
        print(f"Создана привычка: {habit}")
        print(f"Время для выполнения: {habit.time}, {type(habit.time)}")

        if self.request.user.email:
            send_information.delay(self.request.user.email)
        else:
            print("У пользователя нет email, уведомление не отправлено")

        if habit.time and habit.frequency_days:
            try:
                setup_habit_reminder(habit)
                print(f"Напоминание для привычки {habit.pk} настроено")
            except Exception as e:
                print(f"Ошибка настройки напоминания: {e}")

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Обновление привычки"""

        instance = self.get_object()

        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)



class PublicHabitListAPIView(generics.ListAPIView):
    """Представление для списка публичных привычек"""

    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated, ~IsOwnerOnly | IsOwnerOnly]
    pagination_class = HabitsPaginator

    def get_queryset(self) -> QuerySet[Habit]:
        """Фильтрует привычки в зависимости от статуса публичности привычки"""

        user = self.request.user

        if not user.is_authenticated:
            return Habit.objects.none()
        return Habit.objects.filter(is_public=True)
