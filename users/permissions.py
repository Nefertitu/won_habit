from typing import Any, Protocol

from rest_framework import permissions
from rest_framework.request import Request

from users.models import User


class HasOwner(Protocol):
    owner: User


class IsOwnerOnly(permissions.BasePermission):
    """Разрешение только для владельца объекта"""

    def has_object_permission(self, request: Request, view: Any, obj: HasOwner) -> bool:
        """Проверяет, является ли пользователь владельцем объекта"""
        return obj.owner == request.user
