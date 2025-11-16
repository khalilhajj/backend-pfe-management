
from django.test import TestCase
from authentication.models import User, Role
from rest_framework_simplejwt.tokens import RefreshToken

class RoleModelTest(TestCase):
    """Test cases for the Role model"""
    
    def setUp(self):
        """Set up test data that will be used across multiple tests"""
        # import pdb; pdb.set_trace()
        self.role = Role.objects.create(name="Admin")
    
    def test_role_creation(self):
        """Test that a role can be created successfully"""
        self.assertEqual(self.role.name, "Admin")
        self.assertIsNotNone(self.role.id)
    
    def test_role_str_method(self):
        """Test the string representation of a role"""
        self.assertEqual(str(self.role), "Admin")
    
    def test_role_unique_name(self):
        """Test that role names must be unique"""
        with self.assertRaises(Exception):
            Role.objects.create(name="Admin")
    
    def test_role_max_length(self):
        """Test that role name respects max_length constraint"""
        long_name = "a" * 51  # Exceeds max_length of 50
        role = Role(name=long_name)
        with self.assertRaises(Exception):
            role.full_clean()  # This validates the model


class UserModelTest(TestCase):
    """Test cases for the User model"""
    
    def setUp(self):
        """Set up test data"""
        self.role = Role.objects.create(name="Manager")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role=self.role
        )
    
    def test_user_creation(self):
        """Test that a user can be created successfully"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.role, self.role)
        self.assertIsNotNone(self.user.id)
    
    def test_user_str_method(self):
        """Test the string representation of a user"""
        self.assertEqual(str(self.user), "testuser")
    
    def test_user_password_is_hashed(self):
        """Test that passwords are properly hashed"""
        self.assertNotEqual(self.user.password, "testpass123")
        self.assertTrue(self.user.check_password("testpass123"))
    
    def test_user_without_role(self):
        """Test that a user can be created without a role"""
        user_no_role = User.objects.create_user(
            username="noroleuser",
            email="norole@example.com",
            password="testpass123"
        )
        self.assertIsNone(user_no_role.role)
    
    def test_role_deletion_sets_user_role_to_null(self):
        """Test that deleting a role sets user.role to NULL (SET_NULL)"""
        role_id = self.role.id
        self.role.delete()
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertIsNone(self.user.role)
    
    def test_get_token_method(self):
        """Test that get_token returns a valid JWT token with custom claims"""
        token = self.user.get_token()
        
        self.assertIsInstance(token, RefreshToken)
        
        self.assertEqual(token['username'], self.user.username)
        self.assertEqual(token['email'], self.user.email)
        self.assertEqual(token['role_id'], self.role.id)
        self.assertEqual(token['role_name'], self.role.name)
        
        # Verify we can get an access token from it
        access_token = str(token.access_token)
        self.assertIsNotNone(access_token)
        self.assertTrue(len(access_token) > 0)
    
    def test_get_token_without_role(self):
        """Test get_token for a user without a role"""
        user_no_role = User.objects.create_user(
            username="noroleuser",
            email="norole@example.com",
            password="testpass123"
        )
        
        # This should raise an AttributeError because role is None
        with self.assertRaises(AttributeError):
            token = user_no_role.get_token()
    
    def test_user_inherits_from_abstract_user(self):
        """Test that User has AbstractUser fields"""
        self.assertTrue(hasattr(self.user, 'first_name'))
        self.assertTrue(hasattr(self.user, 'last_name'))
        self.assertTrue(hasattr(self.user, 'is_staff'))
        self.assertTrue(hasattr(self.user, 'is_active'))
        self.assertTrue(hasattr(self.user, 'date_joined'))