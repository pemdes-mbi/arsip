from django.core.management.base import BaseCommand
from arsip.google_drive import test_google_apps_script_connection

class Command(BaseCommand):
    help = 'Test connection to Google Apps Script Web App for Google Drive integration'

    def handle(self, *args, **kwargs):
        self.stdout.write("Menguji koneksi ke Google Apps Script...")
        try:
            success = test_google_apps_script_connection()
            if success:
                self.stdout.write(self.style.SUCCESS('Google Apps Script connection: OK'))
            else:
                self.stdout.write(self.style.ERROR('Google Apps Script connection: FAILED'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Google Apps Script connection: FAILED\nError: {str(e)}'))
