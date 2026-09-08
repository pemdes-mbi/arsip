import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arsip.models import Kategori, Arsip

def audit():
    kategori_all = Kategori.objects.all()
    arsip_all = Arsip.objects.select_related('kategori').all()
    
    print("=== TAHAP 37A AUDIT ===")
    print(f"Total Kategori: {kategori_all.count()}")
    print(f"Total Arsip: {arsip_all.count()}")
    
    print("\n--- Daftar Kategori ---")
    for k in kategori_all:
        arsip_count = k.arsip.count()
        print(f"ID: {k.id} | Nama: {k.nama} | Jumlah Arsip: {arsip_count}")
        
    print("\n--- Arsip dan Kategori ---")
    for a in arsip_all:
        kat_nama = a.kategori.nama if a.kategori else "TIDAK ADA KATEGORI (NULL)"
        print(f"Arsip ID: {a.id} | File: {a.nama_file} | Warga: {a.nama_warga} | Kategori: {kat_nama}")

if __name__ == '__main__':
    audit()
