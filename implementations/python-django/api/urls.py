from django.urls import path
from . import views

urlpatterns = [
    path("health", views.HealthView.as_view()),
    path("echo", views.EchoView.as_view()),
    path("users", views.UserListView.as_view()),
    path("users/<int:user_id>", views.UserDetailView.as_view()),
    path("external", views.ExternalAPIView.as_view()),
    path("protected", views.ProtectedView.as_view()),
    path("upload", views.UploadView.as_view()),
]
