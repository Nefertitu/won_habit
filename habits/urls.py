from django.urls import path
from rest_framework.routers import DefaultRouter

from habits.apps import HabitsConfig
from habits.views import (
    HabitViewSet,
    PublicHabitListAPIView,
)

app_name = HabitsConfig.name


router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habits")

urlpatterns = [
    path("public_habit/", PublicHabitListAPIView.as_view(), name="public-habit-list"),
] + router.urls
