import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from authentication.serializers.UserSerializer import UserSerializer
from authentication.serializers.LoginSerializer import LoginSerializer
from authentication.models import Role

User = get_user_model()


@pytest.mark.django_db
class TestUserSerializer:
    """Test cases for UserSerializer"""
    
    def test_user_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        serializer = UserSerializer(user)
        expected_fields = {'id', 'username', 'email', 'password', 'role', 'first_name', 'last_name', 'phone', 'profile_picture'}
        assert set(serializer.data.keys()) == expected_fields - {'password'}

    def test_user_serializer_password_is_write_only(self):
        """Test that password field is write-only and not in output"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        serializer = UserSerializer(user)
        assert 'password' not in serializer.data

    def test_user_serializer_create_with_valid_data(self):
        """Test creating a user with valid data"""
        role = Role.objects.get(name='Student')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'role': role.id,
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '1234567890'
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        user = serializer.save()
        
        assert user.username == 'newuser'
        assert user.email == 'newuser@example.com'
        assert user.check_password('securepass123')
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.phone == '1234567890'
        assert user.role == role

    def test_user_serializer_password_is_hashed(self):
        """Test that password is properly hashed when creating user"""
        data = {
            'username': 'hashtest',
            'email': 'hash@example.com',
            'password': 'plaintextpass123'
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid()
        user = serializer.save()
        
        assert user.password != 'plaintextpass123'
        assert user.check_password('plaintextpass123')

    def test_user_serializer_invalid_email(self):
        """Test that serializer rejects invalid email"""
        data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'testpass123'
        }
        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_user_serializer_missing_required_fields(self):
        """Test that serializer rejects data with missing required fields"""
        data = {
            'username': 'testuser'
        }
        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors or 'password' in serializer.errors

    def test_user_serializer_duplicate_username(self):
        """Test that serializer rejects duplicate username"""
        User.objects.create_user(username='existing', email='existing@example.com', password='pass123')
        data = {
            'username': 'existing',
            'email': 'newemail@example.com',
            'password': 'pass123'
        }
        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors


@pytest.mark.django_db
class TestLoginSerializer:
    """Test cases for LoginSerializer"""
    
    def test_login_serializer_with_valid_credentials(self):
        """Test login with valid username and password"""
        User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='loginpass123'
        )
        data = {
            'username': 'loginuser',
            'password': 'loginpass123'
        }
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()
        validated_user = serializer.validated_data
        assert validated_user.username == 'loginuser'

    def test_login_serializer_with_invalid_password(self):
        """Test login with incorrect password raises AuthenticationFailed"""
        User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='correctpass123'
        )
        data = {
            'username': 'loginuser',
            'password': 'wrongpass123'
        }
        serializer = LoginSerializer(data=data)
        with pytest.raises(AuthenticationFailed) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert 'Invalid username or password' in str(exc_info.value)

    def test_login_serializer_with_nonexistent_user(self):
        """Test login with non-existent username raises AuthenticationFailed"""
        data = {
            'username': 'nonexistent',
            'password': 'somepassword'
        }
        serializer = LoginSerializer(data=data)
        with pytest.raises(AuthenticationFailed) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert 'Invalid username or password' in str(exc_info.value)

    def test_login_serializer_missing_username(self):
        """Test login without username"""
        data = {
            'password': 'somepassword'
        }
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors

    def test_login_serializer_missing_password(self):
        """Test login without password"""
        data = {
            'username': 'someuser'
        }
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_login_serializer_empty_credentials(self):
        """Test login with empty credentials"""
        data = {
            'username': '',
            'password': ''
        }
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors
        assert 'password' in serializer.errors

    def test_login_serializer_password_not_in_output(self):
        """Test that password is write-only and doesn't appear in serialized data"""
        User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='loginpass123'
        )
        data = {
            'username': 'loginuser',
            'password': 'loginpass123'
        }
        serializer = LoginSerializer(data=data)
        serializer.is_valid()
        # Password should not be in the serialized representation
        assert 'password' not in serializer.data