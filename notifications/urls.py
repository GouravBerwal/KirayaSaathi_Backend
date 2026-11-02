from django.urls import path

from .views import (
    NotificationListAPIView,
    NotificationDetailAPIView,
    UnreadNotificationCountAPIView,
    GenerateNotificationsAPIView,
    PendingBillsAPIView,
    SendNotificationMessageAPIView,
    SendBulkNotificationMessagesAPIView,
    NotificationWhatsAppLinkAPIView,
)

urlpatterns = [
    path("", NotificationListAPIView.as_view(), name="notification-list"),
    path(
        "generate/",
        GenerateNotificationsAPIView.as_view(),
        name="generate-notifications",
    ),
    path(
        "unread-count/",
        UnreadNotificationCountAPIView.as_view(),
        name="unread-notification-count",
    ),
    path(
        "pending-bills/",
        PendingBillsAPIView.as_view(),
        name="pending-bills",
    ),
    path(
        "send-bulk/",
        SendBulkNotificationMessagesAPIView.as_view(),
        name="send-bulk-notifications",
    ),
    path(
        "<int:pk>/",
        NotificationDetailAPIView.as_view(),
        name="notification-detail",
    ),
    path(
        "<int:pk>/send/",
        SendNotificationMessageAPIView.as_view(),
        name="send-notification-message",
    ),
    path(
        "<int:pk>/whatsapp-link/",
        NotificationWhatsAppLinkAPIView.as_view(),
        name="notification-whatsapp-link",
    ),
]
