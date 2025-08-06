from rest_framework import serializers

from users.models import User


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Пользователь"""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone",
            "city",
            "avatar",
        )


class PublicUserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели 'PublicUserSerializer'"""

    class Meta:
        model = User
        fields = (
            "email",
            "city",
            "avatar",
        )
