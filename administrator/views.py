from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.db.models import Q

from authentication.models import User, Role
from administrator.Serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    RoleSerializer
)


class ListUsersView(APIView):
    """List all users with filtering and search"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'role',
                openapi.IN_QUERY,
                description="Filter by role ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search by username, email, or name",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'is_active',
                openapi.IN_QUERY,
                description="Filter by active status",
                type=openapi.TYPE_BOOLEAN
            )
        ],
        responses={
            200: UserListSerializer(many=True),
            403: 'Forbidden - Only administrators can access'
        }
    )
    def get(self, request):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can view users.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all users
        users = User.objects.all().select_related('role')
        
        # Filter by role
        role_id = request.query_params.get('role')
        if role_id:
            users = users.filter(role_id=role_id)
        
        # Filter by active status
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            users = users.filter(is_active=is_active_bool)
        
        # Search
        search = request.query_params.get('search')
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Order by date joined (newest first)
        users = users.order_by('-date_joined')
        
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetUserDetailView(APIView):
    """Get detailed information about a specific user"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="User ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: UserDetailSerializer,
            403: 'Forbidden',
            404: 'Not Found'
        }
    )
    def get(self, request, id):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can view user details.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user = get_object_or_404(User, id=id)
        serializer = UserDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateUserView(APIView):
    """Create a new user"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        request_body=UserCreateSerializer,
        responses={
            201: UserDetailSerializer,
            400: 'Bad Request',
            403: 'Forbidden'
        }
    )
    def post(self, request):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can create users.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            detail_serializer = UserDetailSerializer(user)
            return Response({
                'message': 'User created successfully.',
                'data': detail_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateUserView(APIView):
    """Update an existing user"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="User ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        request_body=UserUpdateSerializer,
        responses={
            200: UserDetailSerializer,
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found'
        }
    )
    def patch(self, request, id):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can update users.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user = get_object_or_404(User, id=id)
        
        # Prevent admin from deactivating themselves
        if user.id == request.user.id and 'is_active' in request.data:
            if not request.data.get('is_active'):
                return Response({
                    'error': 'You cannot deactivate your own account.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            detail_serializer = UserDetailSerializer(user)
            return Response({
                'message': 'User updated successfully.',
                'data': detail_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteUserView(APIView):
    """Delete a user (soft delete by deactivating)"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="User ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: 'User deleted successfully',
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found'
        }
    )
    def delete(self, request, id):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can delete users.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user = get_object_or_404(User, id=id)
        
        # Prevent admin from deleting themselves
        if user.id == request.user.id:
            return Response({
                'error': 'You cannot delete your own account.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Soft delete by deactivating
        user.is_active = False
        user.save()
        
        return Response({
            'message': 'User deleted successfully.'
        }, status=status.HTTP_200_OK)


class ResetUserPasswordView(APIView):
    """Reset user password (admin only)"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="User ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        request_body=ChangePasswordSerializer,
        responses={
            200: 'Password reset successfully',
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found'
        }
    )
    def post(self, request, id):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can reset passwords.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user = get_object_or_404(User, id=id)
        
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password reset successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListRolesView(APIView):
    """List all available roles"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        responses={
            200: RoleSerializer(many=True),
            403: 'Forbidden'
        }
    )
    def get(self, request):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can view roles.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetUserStatsView(APIView):
    """Get user statistics"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="User statistics",
                examples={
                    "application/json": {
                        "total_users": 100,
                        "active_users": 85,
                        "inactive_users": 15,
                        "users_by_role": {
                            "Student": 70,
                            "Teacher": 25,
                            "Administrator": 5
                        }
                    }
                }
            ),
            403: 'Forbidden'
        }
    )
    def get(self, request):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can view statistics.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        
        # Users by role
        users_by_role = {}
        roles = Role.objects.all()
        for role in roles:
            count = User.objects.filter(role=role).count()
            users_by_role[role.name] = count
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'users_by_role': users_by_role
        }
        
        return Response(stats, status=status.HTTP_200_OK)