import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from arsip.models import Arsip, Kategori
from django.core.files.uploadedfile import SimpleUploadedFile

def run_audit():
    c = Client()
    print("=== MULAI AUDIT ===")
    
    # 1. TEST 1 - AKSES TANPA LOGIN
    print("\n[TEST 1] AKSES TANPA LOGIN")
    urls_to_test = [
        reverse('arsip:dashboard'),
        reverse('arsip:arsip_list'),
        reverse('arsip:arsip_tambah'),
        reverse('arsip:kategori_list'),
    ]
    all_redirected = True
    for url in urls_to_test:
        response = c.get(url)
        if response.status_code != 302 or 'login' not in response.url:
            print(f"GAGAL: {url} mengembalikan status {response.status_code}")
            all_redirected = False
    
    if all_redirected:
        print("BERHASIL: Semua halaman privat mengalihkan ke login.")
        
    # Setup for logged in tests
    user, created = User.objects.get_or_create(username='testuser')
    if created:
        user.set_password('testpass')
        user.save()
    
    c.login(username='testuser', password='testpass')
    
    # 2. TEST 2 - ID TIDAK ADA
    print("\n[TEST 2] ID TIDAK ADA")
    response_404_1 = c.get('/arsip/999999/')
    response_404_2 = c.get('/arsip/999999/edit/')
    if response_404_1.status_code == 404 and response_404_2.status_code == 404:
        print("BERHASIL: ID tidak ada mengembalikan 404, bukan 500.")
    else:
        print(f"GAGAL: Status detail: {response_404_1.status_code}, edit: {response_404_2.status_code}")
        
    # 3. TEST 3 - ID INVALID
    print("\n[TEST 3] ID INVALID")
    response_invalid = c.get('/arsip/abc/')
    if response_invalid.status_code == 404:
        print("BERHASIL: ID invalid mengembalikan 404.")
    else:
        print(f"GAGAL: Status {response_invalid.status_code}")

    # 4. TEST 4 - CSRF HAPUS
    print("\n[TEST 4] CSRF HAPUS (GET REQUEST)")
    # Create temp record
    kat, _ = Kategori.objects.get_or_create(nama='Test Kat')
    ars, _ = Arsip.objects.get_or_create(nama_warga='Budi', nik='1234', kategori=kat, nama_file='Test file')
    
    response_hapus_get = c.get(f'/arsip/{ars.id}/hapus/')
    if response_hapus_get.status_code == 405: # require_POST
        print("BERHASIL: GET hapus ditolak (405 Method Not Allowed).")
    else:
        print(f"GAGAL: GET hapus tidak 405, status {response_hapus_get.status_code}")
        
    # 5. TEST 6 - INPUT KOSONG
    print("\n[TEST 6] INPUT KOSONG")
    response_tambah_kosong = c.post(reverse('arsip:arsip_tambah'), {})
    if response_tambah_kosong.status_code == 200 and 'This field is required.' in response_tambah_kosong.content.decode():
        # Django form validation failed, returning 200 with form errors
        print("BERHASIL: Input kosong ditolak form.")
    else:
        # Check form errors in context
        if response_tambah_kosong.context and response_tambah_kosong.context['form'].errors:
             print("BERHASIL: Input kosong ditolak form.")
        else:
             print(f"GAGAL: Form mungkin diterima, status {response_tambah_kosong.status_code}")

    # 6. TEST 7 - INPUT PANJANG
    print("\n[TEST 7] INPUT PANJANG")
    long_nik = '1' * 200
    response_tambah_panjang = c.post(reverse('arsip:arsip_tambah'), {
        'nama_warga': 'Test',
        'nik': long_nik,
        'kategori': kat.id,
        'nama_file': 'Test',
    })
    if response_tambah_panjang.status_code == 200 and getattr(response_tambah_panjang, 'context', None):
        print("BERHASIL: Input terlalu panjang ditolak form (tidak crash 500).")
    else:
        print(f"GAGAL: Status {response_tambah_panjang.status_code}")

    # 7. TEST 8 - XSS
    print("\n[TEST 8] XSS")
    ars_xss = Arsip.objects.create(nama_warga="<script>alert('XSS')</script>", nik='111', kategori=kat, nama_file='XSS File')
    response_detail_xss = c.get(f'/arsip/{ars_xss.id}/')
    content = response_detail_xss.content.decode()
    if "<script>alert('XSS')</script>" not in content and "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;" in content:
        print("BERHASIL: XSS escaped di template.")
    else:
        # Check carefully, django by default escapes
        if "<script>alert" not in content.replace(" ", ""):
             print("BERHASIL: XSS tampaknya escaped.")
        else:
             print("GAGAL: Kemungkinan XSS tidak di-escape dengan benar.")

    # 8. TEST 9 - SQL INJECTION
    print("\n[TEST 9] SQL INJECTION")
    response_sql = c.get(reverse('arsip:arsip_list') + "?q=' OR '1'='1")
    if response_sql.status_code == 200:
        print("BERHASIL: SQL Injection melalui pencarian ditangani ORM dengan aman (status 200, tidak crash).")
    else:
        print(f"GAGAL: Status {response_sql.status_code}")

    # 9. TEST 10 - FILE EXTENSION TIDAK DIDUKUNG
    print("\n[TEST 10] EXTENSION FILE")
    bad_file = SimpleUploadedFile("test.exe", b"file_content", content_type="application/octet-stream")
    response_upload_bad = c.post(reverse('arsip:arsip_tambah'), {
        'nama_warga': 'Test Bad File',
        'nik': '111',
        'kategori': kat.id,
        'nama_file': 'Test',
        'file': bad_file
    })
    if getattr(response_upload_bad, 'context', None) and 'file' in response_upload_bad.context['form'].errors:
        print("BERHASIL: Ekstensi file tidak didukung ditolak.")
    else:
        print("GAGAL: File buruk diterima atau error tidak ditangani.")

    # 10. TEST 12 - NAMA FILE ANEH
    print("\n[TEST 12] NAMA FILE ANEH")
    weird_file = SimpleUploadedFile("surat warga (test) 01.pdf", b"pdf content", content_type="application/pdf")
    response_upload_weird = c.post(reverse('arsip:arsip_tambah'), {
        'nama_warga': 'Test Weird File',
        'nik': '111',
        'kategori': kat.id,
        'nama_file': 'Test',
        'file': weird_file
    })
    # Since Google drive upload is mocked out here or would fail (but caught in try-except in views), it will still redirect
    if response_upload_weird.status_code == 302:
        print("BERHASIL: Nama file aneh dapat diproses tanpa crash.")
    else:
        print(f"GAGAL: Status {response_upload_weird.status_code}")

    # 11. TEST 13 - PATH TRAVERSAL
    print("\n[TEST 13] PATH TRAVERSAL")
    traversal_file = SimpleUploadedFile("../../../test.pdf", b"pdf content", content_type="application/pdf")
    response_upload_trav = c.post(reverse('arsip:arsip_tambah'), {
        'nama_warga': 'Test Traversal',
        'nik': '111',
        'kategori': kat.id,
        'nama_file': 'Test',
        'file': traversal_file
    })
    if response_upload_trav.status_code == 302:
        # Check if saved file name is sanitized
        latest_arsip = Arsip.objects.order_by('-id').first()
        if '../' not in latest_arsip.file.name:
            print("BERHASIL: Path traversal ditangani (nama disanitasi).")
        else:
            print("GAGAL: Path traversal mungkin terjadi.")
    else:
        print(f"GAGAL: Status {response_upload_trav.status_code}")
        
    # 12. TEST 14 - FILE LOKAL HILANG
    print("\n[TEST 14] FILE LOKAL HILANG")
    # Make a record with file but delete the file physically
    latest_arsip = Arsip.objects.order_by('-id').first()
    if latest_arsip and latest_arsip.file:
        if os.path.exists(latest_arsip.file.path):
            os.remove(latest_arsip.file.path)
        
        response_detail_hilang = c.get(f'/arsip/{latest_arsip.id}/')
        if response_detail_hilang.status_code == 200:
             print("BERHASIL: File lokal hilang saat detail tidak crash (500).")
        else:
             print(f"GAGAL: Status {response_detail_hilang.status_code}")

if __name__ == '__main__':
    run_audit()
