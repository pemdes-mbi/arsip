from django.db import models
from django.conf import settings

class Kategori(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    drive_folder_id = models.CharField(max_length=255, blank=True, null=True)
    aktif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nama

class Arsip(models.Model):
    nama_warga = models.CharField(max_length=150)
    nik = models.CharField(max_length=16)
    kategori = models.ForeignKey(
        Kategori,
        on_delete=models.PROTECT,
        related_name='arsip'
    )
    nama_file = models.CharField(max_length=255)
    drive_file_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    file = models.FileField(
        upload_to='arsip/%Y/%m/',
        blank=True,
        null=True
    )
    keterangan = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    tanggal_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nama_file
