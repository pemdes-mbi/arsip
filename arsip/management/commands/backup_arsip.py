import os
import zipfile
import logging
import sqlite3
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

logger = logging.getLogger('arsip.backup')

class Command(BaseCommand):
    help = 'Backup database SQLite secara konsisten dan file media ke file arsip ZIP.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Direktori tujuan penyimpanan backup (default: BASE_DIR/backups)'
        )

    def handle(self, *args, **options):
        self.stdout.write('Mulai proses backup database dan media...')
        logger.info("Operasi backup database dan media dimulai.")

        custom_output_dir = options.get('output_dir')
        backup_dir = custom_output_dir if custom_output_dir else os.path.join(settings.BASE_DIR, 'backups')
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
        except Exception as e:
            logger.error("Gagal membuat direktori backup '%s': %s", backup_dir, str(e))
            raise CommandError(f"Direktori backup tidak dapat dibuat: {str(e)}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'arsip_backup_{timestamp}.zip'
        backup_path = os.path.join(backup_dir, backup_filename)

        db_path = str(settings.DATABASES['default']['NAME'])
        media_root = str(settings.MEDIA_ROOT)
        temp_db_snapshot = None

        try:
            # 1. Point-in-time consistent SQLite snapshot
            source_for_zip = db_path
            if os.path.exists(db_path):
                temp_db_snapshot = os.path.join(backup_dir, f'.temp_snap_{timestamp}_{os.path.basename(db_path)}')
                try:
                    src_conn = sqlite3.connect(db_path)
                    dest_conn = sqlite3.connect(temp_db_snapshot)
                    with dest_conn:
                        src_conn.backup(dest_conn)
                    dest_conn.close()
                    src_conn.close()
                    source_for_zip = temp_db_snapshot
                except Exception as snap_err:
                    logger.warning("Tidak dapat membuat live SQLite snapshot (%s), menggunakan file langsung.", str(snap_err))
                    source_for_zip = db_path

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Tambahkan database
                if os.path.exists(source_for_zip):
                    zipf.write(source_for_zip, arcname=os.path.basename(db_path))
                    self.stdout.write(f'Berhasil menambahkan database: {os.path.basename(db_path)}')
                else:
                    self.stdout.write(self.style.WARNING('Database tidak ditemukan!'))

                # Tambahkan file media
                if os.path.exists(media_root):
                    media_count = 0
                    for root, dirs, files in os.walk(media_root):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join('media', os.path.relpath(file_path, media_root))
                            zipf.write(file_path, arcname=arcname)
                            media_count += 1
                    self.stdout.write(f'Berhasil menambahkan direktori media ({media_count} file).')
                else:
                    self.stdout.write(self.style.WARNING('Direktori media tidak ditemukan!'))

                # Tambahkan .env.example sebagai referensi skema environment
                env_example_path = os.path.join(settings.BASE_DIR, '.env.example')
                if os.path.exists(env_example_path):
                    zipf.write(env_example_path, arcname='.env.example')
                    self.stdout.write('Berhasil menambahkan .env.example')

            # Validasi file backup
            if not os.path.exists(backup_path) or not zipfile.is_zipfile(backup_path):
                raise CommandError(f"Hasil backup tidak valid atau rusak: {backup_path}")

            file_size = os.path.getsize(backup_path)
            self.stdout.write(self.style.SUCCESS(f'Backup selesai ({file_size} bytes). Tersimpan di: {backup_path}'))
            logger.info("Backup selesai: %s (ukuran: %s bytes).", backup_filename, file_size)

        except Exception as e:
            logger.error("Proses backup gagal: %s", str(e))
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except Exception:
                    pass
            raise CommandError(f'Backup gagal: {str(e)}')
        finally:
            if temp_db_snapshot and os.path.exists(temp_db_snapshot):
                try:
                    os.remove(temp_db_snapshot)
                except Exception:
                    pass

