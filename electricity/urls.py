from django.urls import path
from . import views
from .views import GenerateElectricityBillAPIView

urlpatterns = [
    path(
        "meters/",
        views.ElectricityMeterListCreateAPIView.as_view(),
        name="electricity-meter-list-create",
    ),
    path(
    "readings/",
    views.MeterReadingListCreateAPIView.as_view(),
    name="meter-reading-list-create",
    ),
    path(
    "bills/",
    views.ElectricityBillListCreateAPIView.as_view(),
    name="electricity-bill-list-create",
    ),
    path("meters/<int:pk>/", views.ElectricityMeterDetailAPIView.as_view(), name="electricity-meter-detail"),
    path("readings/<int:pk>/", views.MeterReadingDetailAPIView.as_view(), name="meter-reading-detail"),
    path("bills/<int:pk>/", views.ElectricityBillDetailAPIView.as_view(), name="electricity-bill-detail"),
    path(
    "bills/generate/",
    GenerateElectricityBillAPIView.as_view(),
    name="generate-electricity-bill",
    ),

]