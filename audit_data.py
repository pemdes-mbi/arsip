import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arsip.models import Arsip

def is_test_data(arsip):
    indicators = ['test', 'dummy', 'xss', 'weird', 'traversal', '<script>', '../', 'tugas']
    
    # Check if any indicator in nama or keterangan or file
    fields_to_check = [arsip.nama_warga, arsip.nama_file, arsip.keterangan, arsip.file.name if arsip.file else '']
    
    for field in fields_to_check:
        if field:
            for ind in indicators:
                if ind.lower() in str(field).lower():
                    return "TEST"
    
    # Check if NIK is exactly '1234567890123456' or similar dummy
    if arsip.nik in ['1234567890123456', '0000000000000000', '1111111111111111']:
        return "TEST"
        
    return "NYATA"

def audit():
    arsips = Arsip.objects.all()
    print("=== AUDIT ARSIP ===")
    
    total = arsips.count()
    test_count = 0
    nyata_count = 0
    
    for a in arsips:
        status = is_test_data(a)
        
        # Override rules based on specific things we know
        if "test" in str(a.nama_warga).lower() or "test" in str(a.nama_file).lower():
            status = "TEST"
        elif status == "NYATA" and not a.drive_file_id:
             # some might be nyata but no drive file id? Or test without it
             pass

        if status == "TEST":
            test_count += 1
        else:
            nyata_count += 1
            status = "PERLU KONFIRMASI" # We treat all non-obvious tests as PERLU KONFIRMASI for safety

        
        
        file_name = a.nama_file
        print(f"ID: {a.id} | Nama: {a.nama_warga} | NIK: {a.nik} | Kategori: {a.kategori.nama if a.kategori else 'None'} | File: {file_name} | Drive ID: {a.drive_file_id} | Status: {status}")

    print(f"\nTotal Arsip: {total}")
    print(f"Total TEST: {test_count}")
    print(f"Total PERLU KONFIRMASI (Bisa jadi NYATA): {nyata_count}")
    
if __name__ == '__main__':
    audit()
