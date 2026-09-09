import os
import zipfile
import shutil
import logging
import sqlite3
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

logger = logging.getLogger('arsip.restore')

class Command(BaseCommand):
    help = 'Restore database SQLite dan file media dari file backup ZIP secara aman.'

    def add_arguments(self, parser):
        parser.add_argument('backup_file', type=str, help='Path ke file backup .zip')
        parser.add_argument('--force', action='store_true', help='Timpa data target tanpa konfirmasi interaktif')
        parser.add_argument('--test-env', action='store_true', help='Restore ke test environment (test_db.sqlite3 & test_media)')

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        force = options['force']
        test_env = options['test_env']

        if not os.path.exists(backup_file):
            logger.error("File backup tidak ditemukan: %s", backup_file)
            raise CommandError(f'File backup tidak ditemukan: {backup_file}')
            
        if not zipfile.is_zipfile(backup_file):
            logger.error("File backup bukan arsip ZIP valid: %s", backup_file)
            raise CommandError(f'File {backup_file} bukan merupakan file ZIP yang valid.')

        target_desc = "TEST ENV (test_db.sqlite3 & test_media)" if test_env else "DATABASE PRODUKSI & MEDIA PRODUKSI"

        if not test_env and not force:
            confirm = input(f'PERINGATAN KRITIS: Restore ini akan menimpa {target_desc}.\nKetik "yes" untuk mengonfirmasi: ')
            if confirm.strip().lower() != 'yes':
                self.stdout.write(self.style.WARNING('Proses restore dibatalkan oleh pengguna.'))
                logger.info("Proses restore dibatalkan oleh pengguna.")
                return

        self.stdout.write(f'Mulai proses restore menuju {target_desc}...')
        logger.info("Memulai restore dari file '%s' menuju target: %s.", os.path.basename(backup_file), target_desc)

        # Direktori sementara untuk ekstraksi yang aman
        temp_dir = os.path.join(settings.BASE_DIR, 'temp_restore')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Proteksi Zip Slip (Path Traversal)
                for member in zipf.infolist():
                    norm_name = os.path.normpath(member.filename)
                    if (norm_name.startswith('..') or os.path.isabs(norm_name) or
                            norm_name.startswith('/') or norm_name.startswith('\\')):
                        raise CommandError(f"File backup memuat path berbahaya: {member.filename}")
                
                zipf.extractall(temp_dir)
            
            db_file_name = os.path.basename(str(settings.DATABASES['default']['NAME']))
            temp_db_path = os.path.join(temp_dir, db_file_name)
            
            # Restore database
            if os.path.exists(temp_db_path):
                if test_env:
                    target_db_path = os.path.join(settings.BASE_DIR, 'test_db.sqlite3')
                    shutil.copy2(temp_db_path, target_db_path)
                    self.stdout.write(self.style.SUCCESS('Berhasil merestore database ke TEST ENV: test_db.sqlite3'))
                else:
                    current_db_path = str(settings.DATABASES['default']['NAME'])
                    if os.path.exists(current_db_path):
                        shutil.copy2(current_db_path, current_db_path + '.old')
                    shutil.copy2(temp_db_path, current_db_path)
                    target_db_path = current_db_path
                    self.stdout.write(self.style.SUCCESS(f'Berhasil merestore database {db_file_name}'))

                # Lakukan integrity check pada SQLite hasil restore
                try:
                    conn = sqlite3.connect(target_db_path)
                    cur = conn.cursor()
                    cur.execute("PRAGMA integrity_check;")
                    check_result = cur.fetchone()[0]
                    conn.close()
                    if check_result.lower() == 'ok':
                        self.stdout.write(self.style.SUCCESS(f'Integrity check database: {check_result}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Peringatan integritas database: {check_result}'))
                except Exception as check_err:
                    logger.warning("Tidak dapat menjalankan PRAGMA integrity_check: %s", str(check_err))
            else:
                self.stdout.write(self.style.WARNING(f'Database {db_file_name} tidak ditemukan di dalam file backup.'))

            # Restore direktori media
            temp_media_dir = os.path.join(temp_dir, 'media')
            if os.path.exists(temp_media_dir):
                if test_env:
                    target_media_dir = os.path.join(settings.BASE_DIR, 'test_media')
                    os.makedirs(target_media_dir, exist_ok=True)
                    shutil.copytree(temp_media_dir, target_media_dir, dirs_exist_ok=True)
                    self.stdout.write(self.style.SUCCESS('Berhasil merestore direktori media ke TEST ENV: test_media'))
                else:
                    current_media_dir = str(settings.MEDIA_ROOT)
                    os.makedirs(current_media_dir, exist_ok=True)
                    shutil.copytree(temp_media_dir, current_media_dir, dirs_exist_ok=True)
                    self.stdout.write(self.style.SUCCESS('Berhasil merestore direktori media'))
            else:
                self.stdout.write(self.style.WARNING('Direktori media tidak ditemukan di dalam file backup.'))

            logger.info("Restore selesai dengan sukses untuk target: %s.", target_desc)
            self.stdout.write(self.style.SUCCESS('Proses restore selesai dengan sukses!'))

        except Exception as e:
            logger.error("Terjadi kegagalan saat proses restore: %s", str(e))
            raise CommandError(f'Terjadi error saat restore: {str(e)}')
        finally:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass

