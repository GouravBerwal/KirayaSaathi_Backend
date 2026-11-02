
from django.urls import path

from .views import DashboardSummaryAPIView

urlpatterns = [
    path(
        "",
        DashboardSummaryAPIView.as_view(),
        name="dashboard-summary",
    ),
]
