from django.db.models.signals import post_migrate
from django.dispatch import receiver
from authentication.models import Role, User

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