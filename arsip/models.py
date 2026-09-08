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

class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    action = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        username = self.user.username if self.user else "Unknown"
        return f"{username} - {self.action} - {self.created_at}"

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib import messages

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        action="LOGIN",
        description="User berhasil login."
    )
    if request and hasattr(request, '_messages'):
        messages.success(request, 'Login berhasil.')

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        AuditLog.objects.create(
            user=user,
            action="LOGOUT",
            description="User logout."
        )
    if request and hasattr(request, '_messages'):
        messages.success(request, 'Anda telah logout.')
