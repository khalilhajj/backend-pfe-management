from django.urls import path
from .views import (
    ListUsersView,
    GetUserDetailView,
    CreateUserView,
    UpdateUserView,
    DeleteUserView,
    ResetUserPasswordView,
    ListRolesView,
    GetUserStatsView,
)

urlpatterns = [
    path('users/', ListUsersView.as_view(), name='list-users'),
    path('users/<int:id>/', GetUserDetailView.as_view(), name='user-detail'),
    path('users/create/', CreateUserView.as_view(), name='create-user'),
    path('users/<int:id>/update/', UpdateUserView.as_view(), name='update-user'),
    path('users/<int:id>/delete/', DeleteUserView.as_view(), name='delete-user'),
    path('users/<int:id>/reset-password/', ResetUserPasswordView.as_view(), name='reset-password'),
    path('roles/', ListRolesView.as_view(), name='list-roles'),
    path('stats/', GetUserStatsView.as_view(), name='user-stats'),
]