from django.urls import reverse
from drf_yasg.inspectors import view
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from users.serializers import UserProfileSerializer


class UserTestCase(APITestCase):
    """Тест кейс для проверки CRUD представлений модели 'User'"""

    def setUp(self) -> None:
        """Инициализация тестовых данных"""

        self.user = User.objects.create(
            email="testuser@example.com",
            tg_chat_id="123456789",
            phone="79994959595",
            city="Moscow",
        )

        self.client.force_authenticate(user=self.user)

    def test_user_retrieve(self) -> None:
        """Тест получения деталей информации о пользователе"""

        url = reverse("users:user-detail", args=(self.user.pk,))
        response = self.client.get(url)
        data = response.json()
        print(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data.get("email"), self.user.email)
        self.assertEqual(data.get("city"), self.user.city)
        self.assertEqual(data.get("phone"), self.user.phone)
        self.assertEqual(True, self.user.is_active)
        self.assertEqual(True, self.user.is_authenticated)
        self.assertEqual(False, self.user.is_superuser)

    def test_user_create(self) -> None:
        """Тест создания нового пользователя"""

        url = reverse("users:user-list")
        data = {
            "email": "newtestuser@example.com",
            "tg_chat_id": "111111111",
            "phone": "79991111111",
            "city": "Krasnodar",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.all().count(), 2)

    def test_user_update(self) -> None:
        """Тест обновления деталей привычки"""

        url = reverse("users:user-detail", args=(self.user.pk,))
        data = {
            "phone": "79992222222",
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(url, data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()

        if hasattr(view, 'get_serializer_class'):
            serializer_class = view.get_serializer_class()
            self.assertEqual(serializer_class.__name__, "UserProfileSerializer")
            self.assertEqual(data.get("phone"), "79992222222")
            self.assertEqual(data.get("id"), self.user.pk)

    def test_user_delete(self) -> None:
        """Тест удаления пользователя"""

        superuser = User.objects.create(
            email="newsuperuser@example.com",
            is_superuser=True,
            is_staff=True
        )
        self.client.force_authenticate(user=superuser)
        user_to_delete = User.objects.create(email="todelete@example.com")

        url = reverse("users:user-detail", args=(user_to_delete.pk,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(pk=user_to_delete.pk)

        self.assertEqual(User.objects.all().count(), 2)


