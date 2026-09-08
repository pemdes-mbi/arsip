import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arsip.models import Kategori, Arsip

def mask_nik(nik):
    if len(nik) >= 8:
        return nik[:4] + "*" * (len(nik) - 8) + nik[-4:]
    return "*" * len(nik)

def run_audit():
    arsip_all = Arsip.objects.select_related('kategori').all()
    kategori_all = Kategori.objects.all()

    master_categories = [
        "Surat Keluar", "Surat Masuk", "SKCK", "Surat Kematian",
        "Surat Kelahiran", "Surat Keterangan Domisili", "Surat Keterangan Tidak Mampu", "Rekomendasi"
    ]

    test_keywords = ["test", "xss"]

    results = []
    
    for a in arsip_all:
        kat_nama = a.kategori.nama if a.kategori else "NULL"
        
        # Check Drive ID
        drive_id = "ADA" if a.drive_file_id else "TIDAK ADA"
        
        # Check File Lokal
        try:
            file_lokal = "ADA" if a.file and os.path.exists(a.file.path) else "TIDAK ADA"
        except ValueError:
            # Sometime a.file.path throws error if file is somehow missing from field
            file_lokal = "TIDAK ADA"
            
        # Determine Candidate
        kandidat = "BELUM DITENTUKAN"
        klasifikasi = "MEMBUTUHKAN KEPUTUSAN USER"
        alasan = ""
        
        is_test = False
        if any(kw in a.nama_file.lower() for kw in test_keywords) or \
           any(kw in kat_nama.lower() for kw in test_keywords) or \
           any(kw in a.nama_warga.lower() for kw in test_keywords):
            is_test = True
            
        if is_test:
            kandidat = "-"
            klasifikasi = "DATA TEST"
            alasan = "Mengandung keyword test/XSS"
        elif kat_nama in master_categories:
            kandidat = kat_nama
            klasifikasi = "SUDAH BENAR"
            alasan = "Sudah menggunakan master kategori"
        elif kat_nama == "SURAT KELAHIRAN/AKTA":
            kandidat = "Surat Kelahiran"
            klasifikasi = "KANDIDAT KUAT"
            alasan = "Nama kategori lama sangat mirip dengan Surat Kelahiran"
        else:
            klasifikasi = "TIDAK JELAS"
            alasan = "Tidak ada bukti cukup untuk menentukan kategori surat"
            
        results.append({
            "id": a.id,
            "nama_warga": a.nama_warga,
            "nik": mask_nik(a.nik),
            "nama_file": a.nama_file,
            "kategori_lama": kat_nama,
            "drive_id": drive_id,
            "file_lokal": file_lokal,
            "kandidat": kandidat,
            "klasifikasi": klasifikasi,
            "alasan": alasan
        })
        
    print(json.dumps({
        "total_kategori": kategori_all.count(),
        "total_arsip": arsip_all.count(),
        "arsip_data": results
    }, indent=2))

if __name__ == "__main__":
    run_audit()
