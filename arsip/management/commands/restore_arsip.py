import os
import zipfile
import shutil
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    help = 'Restore database dan file media dari backup zip.'

    def add_arguments(self, parser):
        parser.add_argument('backup_file', type=str, help='Path ke file backup .zip')
        parser.add_argument('--force', action='store_true', help='Timpa data yang ada tanpa konfirmasi')
        parser.add_argument('--test-env', action='store_true', help='Restore ke test environment (test_db.sqlite3 & test_media)')

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        force = options['force']
        test_env = options['test_env']

        if not os.path.exists(backup_file):
            raise CommandError(f'File backup tidak ditemukan: {backup_file}')
            
        if not zipfile.is_zipfile(backup_file):
            raise CommandError(f'File {backup_file} bukan merupakan file ZIP yang valid.')

        if not force:
            confirm = input(f'PERINGATAN: Restore akan menimpa database dan direktori media Anda saat ini.\nKetik "yes" untuk melanjutkan: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Proses restore dibatalkan.'))
                return

        self.stdout.write('Mulai proses restore...')

        # Ekstrak backup ke direktori sementara
        temp_dir = os.path.join(settings.BASE_DIR, 'temp_restore')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            db_file_name = os.path.basename(settings.DATABASES['default']['NAME'])
            temp_db_path = os.path.join(temp_dir, db_file_name)
            
            # Cek jika ada db.sqlite3 di root arsip
            if os.path.exists(temp_db_path):
                if test_env:
                    target_db_path = os.path.join(settings.BASE_DIR, 'test_db.sqlite3')
                    shutil.copy2(temp_db_path, target_db_path)
                    self.stdout.write(self.style.SUCCESS(f'Berhasil merestore database ke TEST ENV: test_db.sqlite3'))
                else:
                    # Backup database lama (opsional/darurat)
                    current_db_path = settings.DATABASES['default']['NAME']
                    if os.path.exists(current_db_path):
                        shutil.copy2(current_db_path, current_db_path + '.old')
                    
                    shutil.copy2(temp_db_path, current_db_path)
                    self.stdout.write(self.style.SUCCESS(f'Berhasil merestore database {db_file_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Database {db_file_name} tidak ditemukan di backup.'))

            temp_media_dir = os.path.join(temp_dir, 'media')
            if os.path.exists(temp_media_dir):
                if test_env:
                    target_media_dir = os.path.join(settings.BASE_DIR, 'test_media')
                    os.makedirs(target_media_dir, exist_ok=True)
                    shutil.copytree(temp_media_dir, target_media_dir, dirs_exist_ok=True)
                    self.stdout.write(self.style.SUCCESS('Berhasil merestore direktori media ke TEST ENV: test_media'))
                else:
                    current_media_dir = settings.MEDIA_ROOT
                    if os.path.exists(current_media_dir):
                        pass 
                    
                    os.makedirs(current_media_dir, exist_ok=True)
                    shutil.copytree(temp_media_dir, current_media_dir, dirs_exist_ok=True)
                    self.stdout.write(self.style.SUCCESS('Berhasil merestore direktori media'))
            else:
                self.stdout.write(self.style.WARNING('Direktori media tidak ditemukan di backup.'))

        except Exception as e:
            raise CommandError(f'Terjadi error saat restore: {str(e)}')
        finally:
            # Bersihkan temporary dir
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
        self.stdout.write(self.style.SUCCESS('Proses restore selesai!'))
