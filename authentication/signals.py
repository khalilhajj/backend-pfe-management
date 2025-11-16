from django.db.models.signals import post_migrate
from django.dispatch import receiver
from authentication.models import Role, User
from faker import Faker
import random
fake = Faker()

@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    # Only run for your app
    if sender.name == 'authentication':
        default_roles = ['Student', 'Teacher', 'Administrator', 'Company']
        for role_name in default_roles:
            Role.objects.get_or_create(name=role_name)

@receiver(post_migrate)
def create_default_user(sender, **kwargs):
    if sender.name == 'authentication':
        admin_role = Role.objects.get(name='Administrator')
        user, created = User.objects.get_or_create(
            username='admin',
            email='admin@admin.com',
            role=admin_role
        )
        if created:
            user.set_password('admin')
            user.save()

@receiver(post_migrate)
def create_fake_users(sender, **kwargs):
    if sender.name == 'authentication':
        if User.objects.exists():
            return 
        roles = ['Administrator', 'Teacher', 'Student', 'Company']
        for role_name in roles:
            Role.objects.get_or_create(name=role_name)

        all_roles = list(Role.objects.all())
        for _ in range(1000):
            role = random.choice(all_roles)
            user = User(
                username=fake.user_name(),
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=role
            )
            user.set_password("12345678")
            user.save()

        print("Created 20 fake users!")