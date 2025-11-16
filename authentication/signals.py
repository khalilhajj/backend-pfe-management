from django.db.models.signals import post_migrate
from django.dispatch import receiver
from authentication.models import Role

@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    # Only run for your app
    if sender.name == 'authentication':
        default_roles = ['Student', 'Teacher', 'Administrator', 'Company']
        for role_name in default_roles:
            Role.objects.get_or_create(name=role_name)