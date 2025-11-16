from rest_framework import serializers
from authentication.models import User, Role
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']
        ref_name = 'AuthRole'

class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'profile_picture', 'role', 'role_name',
            'is_active', 'date_joined'
        ]
        read_only_fields = ['date_joined']
        ref_name = 'AuthUserList'

class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed user view"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'profile_picture', 'role', 'role_name',
            'is_active', 'is_staff', 'date_joined', 'last_login'
        ]
        read_only_fields = ['date_joined', 'last_login']

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'profile_picture',
            'role', 'is_active'
        ]
    
    def validate_username(self, value):
        """Validate username uniqueness and format"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        
        if not value.isalnum() and '_' not in value:
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, and underscores."
            )
        
        return value.lower()
    
    def validate_email(self, value):
        """Validate email uniqueness and format"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        
        return value.lower()
    
    def validate_password(self, value):
        """Validate password strength"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing users"""
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone',
            'profile_picture', 'role', 'is_active'
        ]
    
    def validate_email(self, value):
        """Validate email uniqueness (excluding current user)"""
        user = self.instance
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email already exists.")
        
        return value.lower()

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password reset by admin"""
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    class Meta:
        ref_name = 'AuthChangePassword'
    def validate_new_password(self, value):
        """Validate password strength"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "Passwords do not match."
            })
        
        return attrs