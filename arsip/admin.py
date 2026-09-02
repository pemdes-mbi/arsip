from django.contrib import admin
from .models import Kategori, Arsip

@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ('nama', 'aktif', 'drive_folder_id', 'created_at', 'updated_at')
    list_filter = ('aktif',)
    search_fields = ('nama',)

@admin.register(Arsip)
class ArsipAdmin(admin.ModelAdmin):
    list_display = ('nama_warga', 'nik', 'kategori', 'nama_file', 'uploaded_by', 'tanggal_upload')
    list_filter = ('kategori', 'tanggal_upload')
    search_fields = ('nama_warga', 'nik', 'nama_file')
