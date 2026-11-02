
from django.urls import path

from .views import ReportsAPIView

urlpatterns = [
    path("", ReportsAPIView.as_view(), name="reports-summary"),
]
