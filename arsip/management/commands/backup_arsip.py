import os
import zipfile
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import shutil

class Command(BaseCommand):
    help = 'Backup database dan file media.'

    def handle(self, *args, **options):
        self.stdout.write('Mulai proses backup...')

        # Pastikan direktori backups ada
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Generate nama file backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'arsip_backup_{timestamp}.zip'
        backup_path = os.path.join(backup_dir, backup_filename)

        db_path = settings.DATABASES['default']['NAME']
        media_root = settings.MEDIA_ROOT
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup database
            if os.path.exists(db_path):
                zipf.write(db_path, arcname=os.path.basename(db_path))
                self.stdout.write(f'Berhasil menambahkan database: {os.path.basename(db_path)}')
            else:
                self.stdout.write(self.style.WARNING('Database tidak ditemukan!'))

            # Backup media files
            if os.path.exists(media_root):
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join('media', os.path.relpath(file_path, media_root))
                        zipf.write(file_path, arcname=arcname)
                self.stdout.write('Berhasil menambahkan direktori media.')
            else:
                self.stdout.write(self.style.WARNING('Direktori media tidak ditemukan!'))
                
            # Backup .env.example
            env_example_path = os.path.join(settings.BASE_DIR, '.env.example')
            if os.path.exists(env_example_path):
                zipf.write(env_example_path, arcname='.env.example')
                self.stdout.write('Berhasil menambahkan .env.example')

        self.stdout.write(self.style.SUCCESS(f'Backup selesai. File tersimpan di: {backup_path}'))
