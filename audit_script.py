import os
import json
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arsip.models import Arsip, Kategori

arsips = Arsip.objects.all().select_related('kategori').order_by('id')
result_arsip = []
for a in arsips:
    nik = a.nik
    if len(nik) > 4:
        masked_nik = nik[:2] + 'x' * (len(nik) - 4) + nik[-2:]
    else:
        masked_nik = 'x' * len(nik)
        
    has_drive = 'YA' if a.drive_file_id else 'TIDAK'
    
    file_exists = 'TIDAK'
    if a.file:
        try:
            if os.path.exists(a.file.path):
                file_exists = 'YA'
        except Exception:
            pass
            
    tz = timezone.localtime(a.tanggal_upload).strftime('%Y-%m-%d %H:%M:%S')
    
    result_arsip.append({
        'id': a.id,
        'nama_warga': a.nama_warga,
        'nik': masked_nik,
        'nama_file': a.nama_file,
        'kategori': a.kategori.nama if a.kategori else 'None',
        'drive': has_drive,
        'lokal': file_exists,
        'tanggal': tz
    })

print('===ARSIP_DATA===')
print(json.dumps(result_arsip, indent=2))

kats = Kategori.objects.all().order_by('id')
result_kat = []
for k in kats:
    count = k.arsip.count()
    result_kat.append({
        'id': k.id,
        'nama': k.nama,
        'count': count
    })

print('===KATEGORI_DATA===')
print(json.dumps(result_kat, indent=2))
