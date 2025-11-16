from django.db.models.signals import post_migrate
from django.dispatch import receiver
from authentication.models import Role

User = get_user_model()

@receiver(post_migrate)
def create_roles_and_initial_admin(sender, **kwargs):
    # Only run for this app
    if getattr(sender, "name", "") != 'authentication':
        return

    try:
        # Create default roles
        default_roles = ['Student', 'Teacher', 'Administrator', 'Company']
        for role_name in default_roles:
            Role.objects.get_or_create(name=role_name)

        # Ensure role with id=3 exists (Administrator)
        admin_role, _ = Role.objects.get_or_create(pk=3, defaults={'name': 'Administrator'})

        # If any user exists, do not create initial admin
        if User.objects.exists():
            return

        # Create initial admin user (regular user, not superuser)
        username = os.environ.get('DJANGO_ADMIN_USERNAME', 'admin')
        email = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_ADMIN_PASSWORD')
        if not password:
            password = secrets.token_urlsafe(16)
            print(f'[initial admin] generated password for {username}: {password}')

        user = User.objects.create(
            username=username,
            first_name='Admin',
            last_name='User',
            password='admin',
            email=email,
            role=3,
        )
        user.set_password(password)
        user.save()
        print(f'[initial admin] created admin user "{username}" with role id={admin_role.pk}')
    except (OperationalError, ProgrammingError) as e:
        print('create_roles_and_initial_admin skipped (DB not ready):', e)
    except Exception as e:
        print('create_roles_and_initial_admin error:', e)
    if sender.name != 'authentication':
        return

    try:
        # Create default roles
        default_roles = ['Student', 'Teacher', 'Administrator', 'Company']
        for role_name in default_roles:
            Role.objects.get_or_create(name=role_name)

        # Ensure role with id=3 exists (Administrator)
        admin_role, _ = Role.objects.get_or_create(pk=3, defaults={'name': 'Administrator'})

        # If any user exists, do not create initial admin
        if User.objects.exists():
            return

        # Create initial superuser
        username = os.environ.get('DJANGO_ADMIN_USERNAME', 'admin')
        email = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_ADMIN_PASSWORD')
        if not password:
            password = secrets.token_urlsafe(16)
            print(f'[initial admin] generated password for {username}: {password}')

        user = User.objects.create(
            username=username,
            email=email,
            is_staff=True,
            is_superuser=True,
            role=admin_role,
        )
        user.set_password(password)
        user.save()
        print(f'[initial admin] created superuser "{username}" with role id={admin_role.pk}')
    except (OperationalError, ProgrammingError) as e:
        # DB not ready yet (migrations not applied) — skip
        print('create_roles_and_initial_admin skipped (DB not ready):', e)
    except Exception as e:
        # Avoid blocking startup; log/print error
        print('create_roles_and_initial_admin error:', e)

