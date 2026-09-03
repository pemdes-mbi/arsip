import os
import shutil
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Copy template db if on serverless and db.sqlite3 exists in BASE_DIR
try:
    from django.conf import settings
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
        target_db = Path(settings.DATABASES['default']['NAME'])
        source_db = settings.BASE_DIR / 'db.sqlite3'
        if target_db != source_db and not target_db.exists() and source_db.exists():
            target_db.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_db, target_db)
except Exception as e:
    print(f"Warning during db copy: {e}")

application = get_wsgi_application()
app = application

# Auto-migrate and ensure default superuser and categories exist on startup
try:
    from django.core.management import call_command
    from django.db import connection
    
    # Check if migrations are needed
    existing_tables = connection.introspection.table_names()
    if 'auth_user' not in existing_tables:
        call_command('migrate', interactive=False)
    
    # Ensure default superuser exists
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin_user = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    admin_pass = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
    admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@desa.id')
    
    if not User.objects.filter(username=admin_user).exists():
        User.objects.create_superuser(
            username=admin_user,
            email=admin_email,
            password=admin_pass
        )

    # Seed default categories if none exist
    from arsip.models import Kategori
    if not Kategori.objects.exists():
        for kat in ['Kartu Keluarga', 'KTP', 'Surat Keterangan', 'Akta Kelahiran', 'Surat Kematian']:
            Kategori.objects.get_or_create(nama=kat)
except Exception as e:
    print(f"Auto-init database error: {e}")

