import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arsip.models import Arsip

def is_test_data(arsip):
    indicators = ['test', 'dummy', 'xss', 'weird', 'traversal', '<script>', '../', 'tugas']
    
    fields_to_check = [arsip.nama_warga, arsip.nama_file, arsip.keterangan, arsip.file.name if arsip.file else '']
    
    for field in fields_to_check:
        if field:
            for ind in indicators:
                if ind.lower() in str(field).lower():
                    return True
    
    if arsip.nik in ['1234567890123456', '0000000000000000', '1111111111111111']:
        return True
        
    return False

def clean():
    arsips = Arsip.objects.all()
    print("=== PEMBERSIHAN ARSIP TEST ===")
    
    keep_ids = [1, 2, 8, 9, 10]
    
    deleted_records = []
    
    for a in arsips:
        if a.id in keep_ids:
            continue
            
        status = False
        if is_test_data(a):
            status = True
        elif "test" in str(a.nama_warga).lower() or "test" in str(a.nama_file).lower():
            status = True
            
        # Also remove those explicit PREVIEW1, etc NIKs from the previous run
        if str(a.nik).startswith('PREVIEW') or str(a.nik) in ['111', '1234']:
            status = True

        if status:
            deleted_records.append({
                'id': a.id,
                'nama': a.nama_warga,
                'file': a.file.name if a.file else '',
                'drive': a.drive_file_id
            })
            
            # Hapus file lokal
            if a.file:
                try:
                    if os.path.exists(a.file.path):
                        os.remove(a.file.path)
                except Exception:
                    pass
            
            # Hapus dari db
            a.delete()
            
    print(f"Total Dihapus: {len(deleted_records)}")
    for d in deleted_records:
        print(f"Hapus ID: {d['id']} | Nama: {d['nama']} | File: {d['file']} | Drive: {d['drive']}")
        
if __name__ == '__main__':
    clean()
