from typing import Any, List

from rest_framework import permissions, serializers, viewsets
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.serializers import BaseSerializer

from users.models import User
from users.permissions import IsOwnerOnly
from users.serializers import PublicUserSerializer, UserProfileSerializer


class UserCreateApiView(CreateAPIView):
    """Класс для создания профиля пользователя"""

    serializer_class = UserProfileSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Метод для создания профиля пользователя (POST /register/)"""

        user = serializer.save(is_active=True)
        user.set_password(user.password)
        user.save()


class UserProfileViewSet(viewsets.ModelViewSet):
    """Управление пользователями (требуется аутентификация)"""

    serializer_class = UserProfileSerializer
    queryset = User.objects.all()

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        """Динамический выбор сериализатора"""

        print(f"Action: {self.action}")  # Добавьте это
        print(f"User: {self.request.user}")  # И это
        print(f"Is superuser: {self.request.user.is_superuser}")

        if self.action == "list":
            if not self.request.user.is_superuser:
                return PublicUserSerializer

        if self.action == "retrieve":
            object = self.get_object()
            print(f"Request user: {self.request.user.email}, Object user: {object.email}")
            if self.request.user.is_superuser or self.request.user.email == object.email:
                return UserProfileSerializer

        return PublicUserSerializer

    def get_permissions(self) -> List[permissions.BasePermission]:
        """
        Управление разрешениями:
        (GET /users/        # Список
        GET /users/{id}/    # Просмотр
        PUT /users/{id}/    # Полное обновление (только владелец)
        PATCH /users/{id}/  # Частичное обновление (только владелец)
        DELETE /users/{id}/ # Удаление (только админы)
        )
        """

        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        elif self.action == "destroy":
            return [permissions.IsAdminUser()]
        elif self.action in ["update", "partial_update"]:
            return [IsOwnerOnly()]
        return [permissions.IsAuthenticated()]
