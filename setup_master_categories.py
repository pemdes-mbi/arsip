import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arsip.models import Kategori

def setup():
    targets = [
        "Surat Keluar",
        "Surat Masuk",
        "SKCK",
        "Surat Kematian",
        "Surat Kelahiran",
        "Surat Keterangan Domisili",
        "Surat Keterangan Tidak Mampu",
        "Rekomendasi"
    ]
    
    # Existing ones that need renaming to match target (case-insensitive or close)
    # We will just rely on exact matches or create new. 
    # But wait, SQLite might throw IntegrityError if we try to create "Surat Keluar" when "SURAT KELUAR" exists.
    # So let's handle case-insensitive get.
    
    for target in targets:
        # Try to find a case-insensitive match
        kats = Kategori.objects.filter(nama__iexact=target)
        if kats.exists():
            k = kats.first()
            k.nama = target
            k.aktif = True
            k.save()
            print(f"Updated existing category to exact case: {target}")
        else:
            # Create new
            Kategori.objects.create(nama=target, aktif=True)
            print(f"Created new category: {target}")
            
    # Set all others to inactive
    others = Kategori.objects.exclude(nama__in=targets)
    count = others.update(aktif=False)
    print(f"Deactivated {count} other categories.")

if __name__ == '__main__':
    setup()
