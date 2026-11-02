
from django.urls import path

from . import views
from .views import WorkspaceSettingsView


urlpatterns = [
    # Properties
    path(
        "",
        views.PropertyListCreateAPIView.as_view(),
        name="property-list-create",
    ),
    path(
        "<int:pk>/",
        views.PropertyDetailAPIView.as_view(),
        name="property-detail",
    ),

    # Rooms
    path(
        "rooms/",
        views.RoomListCreateAPIView.as_view(),
        name="room-list-create",
    ),
    path(
        "rooms/<int:pk>/",
        views.RoomDetailAPIView.as_view(),
        name="room-detail",
    ),

    # Workspace Settings
    path(
        "settings/",
        WorkspaceSettingsView.as_view(),
        name="workspace-settings",
    ),
]
