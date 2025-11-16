from django.shortcuts import render
from authentication.serializers.LoginSerializer import LoginSerializer
from authentication.serializers.UserSerializer import UserSerializer
from authentication.serializers.ChangePasswordSerializer import ChangePasswordSerializer
from authentication.models import User
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser

class LoginView(APIView):
    permission_classes = [AllowAny] 
    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data
        refresh = RefreshToken.for_user(user)
        token = user.get_token()
        return Response({
            'refresh': str(refresh),
            'access': str(token.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.name if user.role else None,
            },
        })
    
class AddUserView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]
    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.name if user.role else None,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GetUserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response({
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.name if user.role else None,
            }, status=status.HTTP_201_CREATED)

class UpdateUserView(APIView):
    """Update authenticated user's profile information"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(request_body=UserSerializer)
    def put(self, request):
        user = request.user
        # Prevent password updates through this endpoint
        data = request.data.copy()
        if 'password' in data:
            data.pop('password')
        
        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'role': user.role.name if user.role else None,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(request_body=UserSerializer)
    def patch(self, request):
        """Partial update of user profile"""
        user = request.user
        # Prevent password updates through this endpoint
        data = request.data.copy()
        if 'password' in data:
            data.pop('password')
        
        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'role': user.role.name if user.role else None,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAccountView(APIView):
    """Delete authenticated user's account"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        user = request.user
        username = user.username
        
        # Hard delete the user account
        user.delete()
        
        return Response({
            'message': f'Account {username} has been successfully deleted.'
        }, status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    """Change authenticated user's password"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        
        # Verify old password
        if not user.check_password(old_password):
            return Response({
                'old_password': ['Old password is incorrect.']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)