from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Kategori, Arsip, AuditLog
from .forms import KategoriForm, ArsipForm
from django.conf import settings
from django.utils import timezone
from django.db.models import Count
import csv
from django.http import HttpResponse
from datetime import datetime
@login_required
def dashboard(request):
    total_arsip = Arsip.objects.count()
    total_kategori = Kategori.objects.count()
    
    # Arsip Bulan Ini & Tahun Ini
    now = timezone.localtime(timezone.now()) if getattr(settings, 'USE_TZ', False) else timezone.now()
    arsip_bulan_ini = Arsip.objects.filter(tanggal_upload__year=now.year, tanggal_upload__month=now.month).count()
    arsip_tahun_ini = Arsip.objects.filter(tanggal_upload__year=now.year).count()
    
    # Arsip Terbaru
    arsip_terbaru = Arsip.objects.all().order_by('-tanggal_upload')[:5]
    
    # Distribusi Kategori
    statistik_kategori = Kategori.objects.annotate(jumlah_arsip=Count('arsip')).order_by('-jumlah_arsip')
    
    # Statistik Jenis File (in Python to avoid db specific string functions)
    arsip_all = Arsip.objects.values_list('nama_file', flat=True)
    statistik_file = {'PDF': 0, 'Word': 0, 'Excel': 0, 'Image': 0, 'CSV': 0, 'Lainnya': 0}
    for file_name in arsip_all:
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        if ext == 'pdf':
            statistik_file['PDF'] += 1
        elif ext in ['doc', 'docx']:
            statistik_file['Word'] += 1
        elif ext in ['xls', 'xlsx']:
            statistik_file['Excel'] += 1
        elif ext in ['jpg', 'jpeg', 'png']:
            statistik_file['Image'] += 1
        elif ext == 'csv':
            statistik_file['CSV'] += 1
        else:
            statistik_file['Lainnya'] += 1
            
    # Aktivitas Terbaru
    aktivitas_terbaru = AuditLog.objects.all().order_by('-created_at')[:5]
    
    return render(request, 'dashboard/index.html', {
        'total_arsip': total_arsip,
        'total_kategori': total_kategori,
        'arsip_bulan_ini': arsip_bulan_ini,
        'arsip_tahun_ini': arsip_tahun_ini,
        'arsip_terbaru': arsip_terbaru,
        'statistik_kategori': statistik_kategori,
        'statistik_file': statistik_file,
        'aktivitas_terbaru': aktivitas_terbaru
    })

@login_required
def kategori_list(request):
    query = request.GET.get('q', '')
    if query:
        kategori_list = Kategori.objects.filter(nama__icontains=query).order_by('-created_at')
    else:
        kategori_list = Kategori.objects.all().order_by('-created_at')
    
    return render(request, 'kategori/daftar.html', {
        'kategori_list': kategori_list,
        'query': query
    })

@login_required
def kategori_tambah(request):
    if request.method == 'POST':
        form = KategoriForm(request.POST)
        if form.is_valid():
            kategori = form.save(commit=False)
            kategori.aktif = True
            kategori.save()
            messages.success(request, 'Kategori berhasil ditambahkan.')
            return redirect('arsip:kategori_list')
    else:
        form = KategoriForm()
    
    return render(request, 'kategori/tambah.html', {'form': form})

@login_required
def kategori_edit(request, id):
    kategori = get_object_or_404(Kategori, pk=id)
    if request.method == 'POST':
        form = KategoriForm(request.POST, instance=kategori)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kategori berhasil diperbarui.')
            return redirect('arsip:kategori_list')
    else:
        form = KategoriForm(instance=kategori)
    
    return render(request, 'kategori/edit.html', {
        'form': form,
        'kategori': kategori
    })

@login_required
@require_POST
def kategori_toggle(request, id):
    kategori = get_object_or_404(Kategori, pk=id)
    kategori.aktif = not kategori.aktif
    kategori.save()
    status = 'diaktifkan' if kategori.aktif else 'dinonaktifkan'
    messages.success(request, f'Kategori "{kategori.nama}" berhasil {status}.')
    return redirect('arsip:kategori_list')

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def arsip_list(request):
    query = request.GET.get('q', '')
    kategori_id = request.GET.get('kategori', '')
    tanggal_dari = request.GET.get('tanggal_dari', '')
    tanggal_sampai = request.GET.get('tanggal_sampai', '')
    
    arsip_qs = Arsip.objects.all().order_by('-tanggal_upload')
    
    if query:
        arsip_qs = arsip_qs.filter(
            Q(nama_warga__icontains=query) |
            Q(nik__icontains=query) |
            Q(nama_file__icontains=query)
        )
        
    if kategori_id:
        arsip_qs = arsip_qs.filter(kategori_id=kategori_id)
        
    if tanggal_dari:
        try:
            arsip_qs = arsip_qs.filter(tanggal_upload__date__gte=tanggal_dari)
        except (ValueError, TypeError):
            pass
            
    if tanggal_sampai:
        try:
            arsip_qs = arsip_qs.filter(tanggal_upload__date__lte=tanggal_sampai)
        except (ValueError, TypeError):
            pass
            
    kategori_aktif = Kategori.objects.filter(aktif=True)
    
    paginator = Paginator(arsip_qs, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    return render(request, 'arsip/daftar.html', {
        'arsip_list': page_obj,  # Pass page_obj instead of queryset for template backward compatibility if it iterates over it directly, but page_obj is better passed as page_obj
        'page_obj': page_obj,
        'query': query,
        'kategori_id': str(kategori_id),
        'tanggal_dari': tanggal_dari,
        'tanggal_sampai': tanggal_sampai,
        'kategori_aktif': kategori_aktif
    })

@login_required
def arsip_tambah(request):
    if request.method == 'POST':
        form = ArsipForm(request.POST, request.FILES)
        if form.is_valid():
            arsip = form.save(commit=False)
            arsip.uploaded_by = request.user
            arsip.save()
            
            # Google Drive Upload
            if arsip.file:
                try:
                    file_path = arsip.file.path
                    kategori = arsip.kategori.nama
                    nama_file = request.FILES['file'].name
                    mime_type = request.FILES['file'].content_type
                    
                    from .google_drive import upload_to_google_drive
                    drive_response = upload_to_google_drive(file_path, kategori, nama_file, mime_type)
                    
                    arsip.drive_file_id = drive_response['file_id']
                    arsip.save(update_fields=['drive_file_id'])
                    
                    messages.success(request, 'Arsip berhasil disimpan dan diupload ke Google Drive.')
                except Exception as e:
                    messages.warning(request, f'Arsip berhasil disimpan, tetapi upload ke Google Drive gagal. Error: {str(e)}')
            else:
                messages.success(request, 'Arsip berhasil ditambahkan.')
                
            AuditLog.objects.create(
                user=request.user,
                action="CREATE_ARCHIVE",
                description=f"Arsip ID {arsip.id} dibuat. Warga: {arsip.nama_warga}, File: {arsip.nama_file}"
            )
                
            return redirect('arsip:arsip_list')
    else:
        form = ArsipForm()
    
    return render(request, 'arsip/tambah.html', {'form': form})

@login_required
def arsip_detail(request, id):
    arsip = get_object_or_404(Arsip, pk=id)
    
    file_type = None
    file_exists = False
    
    if arsip.file:
        import os
        try:
            if os.path.exists(arsip.file.path):
                file_exists = True
        except Exception:
            file_exists = False
            
        if file_exists:
            ext = os.path.splitext(arsip.file.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                file_type = 'image'
            elif ext == '.pdf':
                file_type = 'pdf'
            else:
                file_type = 'unsupported'
            
    return render(request, 'arsip/detail.html', {
        'arsip': arsip,
        'file_type': file_type,
        'file_exists': file_exists
    })

@login_required
def arsip_edit(request, id):
    arsip = get_object_or_404(Arsip, pk=id)
    if request.method == 'POST':
        form = ArsipForm(request.POST, request.FILES, instance=arsip)
        if form.is_valid():
            has_new_file = 'file' in request.FILES
            
            arsip = form.save()
            
            if has_new_file:
                # Upload the new file to Google Drive
                try:
                    file_path = arsip.file.path
                    kategori = arsip.kategori.nama
                    nama_file = request.FILES['file'].name
                    mime_type = request.FILES['file'].content_type
                    
                    from .google_drive import upload_to_google_drive
                    drive_response = upload_to_google_drive(file_path, kategori, nama_file, mime_type)
                    
                    arsip.drive_file_id = drive_response['file_id']
                    arsip.save(update_fields=['drive_file_id'])
                    
                    messages.success(request, 'Arsip berhasil diperbarui dan file baru diupload ke Google Drive.')
                except Exception as e:
                    messages.warning(request, f'Arsip berhasil diperbarui, tetapi file baru gagal diupload ke Google Drive. Error: {str(e)}')
            else:
                messages.success(request, 'Arsip berhasil diperbarui.')
                
            AuditLog.objects.create(
                user=request.user,
                action="UPDATE_ARCHIVE",
                description=f"Arsip ID {arsip.id} diperbarui. File: {arsip.nama_file}"
            )
                
            return redirect('arsip:arsip_list')
    else:
        form = ArsipForm(instance=arsip)
    
    return render(request, 'arsip/edit.html', {
        'form': form,
        'arsip': arsip
    })

import os

@login_required
@require_POST
def arsip_hapus(request, id):
    arsip = get_object_or_404(Arsip, pk=id)
    
    # Hapus file lokal jika ada
    if arsip.file:
        try:
            if os.path.exists(arsip.file.path):
                os.remove(arsip.file.path)
        except Exception:
            pass
            
    # Hapus record database (file Google Drive dipertahankan)
    AuditLog.objects.create(
        user=request.user,
        action="DELETE_ARCHIVE",
        description=f"Arsip ID {arsip.id} dihapus. Warga: {arsip.nama_warga}, File: {arsip.nama_file}"
    )
    arsip.delete()
    
    messages.success(request, 'Arsip berhasil dihapus dari sistem.')
    return redirect('arsip:arsip_list')

from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from .forms import UserAddForm, UserEditForm

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin, login_url='/')
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'arsip/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin, login_url='/')
def user_add(request):
    if request.method == 'POST':
        form = UserAddForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_superuser = (form.cleaned_data['role'] == 'admin')
            user.is_staff = user.is_superuser
            user.save()
            AuditLog.objects.create(
                user=request.user,
                action="CREATE_USER",
                description=f"User baru dibuat: {user.username}"
            )
            messages.success(request, 'User berhasil dibuat.')
            return redirect('arsip:user_list')
    else:
        form = UserAddForm()
    return render(request, 'arsip/user_form.html', {'form': form, 'title': 'Tambah User'})

@login_required
@user_passes_test(is_admin, login_url='/')
def user_edit(request, id):
    user_obj = get_object_or_404(User, pk=id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.is_superuser = (form.cleaned_data['role'] == 'admin')
            user.is_staff = user.is_superuser
            user.save()
            AuditLog.objects.create(
                user=request.user,
                action="UPDATE_USER",
                description=f"Data user diperbarui: {user.username}"
            )
            messages.success(request, 'User berhasil diperbarui.')
            return redirect('arsip:user_list')
    else:
        form = UserEditForm(instance=user_obj)
    return render(request, 'arsip/user_form.html', {'form': form, 'title': 'Edit User', 'user_obj': user_obj})

@login_required
@user_passes_test(is_admin, login_url='/')
@require_POST
def user_toggle(request, id):
    user_obj = get_object_or_404(User, pk=id)
    
    # Proteksi: tidak boleh menonaktifkan admin terakhir
    if user_obj.is_superuser and user_obj.is_active:
        active_admins = User.objects.filter(is_superuser=True, is_active=True).count()
        if active_admins <= 1:
            messages.error(request, 'Gagal menonaktifkan. Sistem harus memiliki setidaknya satu admin aktif.')
            return redirect('arsip:user_list')
            
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    status = 'diaktifkan' if user_obj.is_active else 'dinonaktifkan'
    action_type = "ACTIVATE_USER" if user_obj.is_active else "DEACTIVATE_USER"
    AuditLog.objects.create(
        user=request.user,
        action=action_type,
        description=f"User {user_obj.username} {status}."
    )
    messages.success(request, f'User {user_obj.username} berhasil {status}.')
    return redirect('arsip:user_list')

@login_required
@user_passes_test(is_admin, login_url='/')
def audit_log(request):
    logs = AuditLog.objects.all().order_by('-created_at')
    
    query = request.GET.get('q', '')
    if query:
        logs = logs.filter(
            Q(user__username__icontains=query) |
            Q(action__icontains=query) |
            Q(description__icontains=query)
        )
        
    return render(request, 'arsip/audit_log.html', {'logs': logs, 'query': query})

def _get_arsip_filtered_qs(request):
    query = request.GET.get('q', '')
    kategori_id = request.GET.get('kategori', '')
    tanggal_dari = request.GET.get('tanggal_dari', '')
    tanggal_sampai = request.GET.get('tanggal_sampai', '')
    
    arsip_qs = Arsip.objects.all().order_by('-tanggal_upload')
    
    if query:
        arsip_qs = arsip_qs.filter(
            Q(nama_warga__icontains=query) |
            Q(nik__icontains=query) |
            Q(nama_file__icontains=query)
        )
        
    if kategori_id:
        arsip_qs = arsip_qs.filter(kategori_id=kategori_id)
        
    if tanggal_dari:
        try:
            arsip_qs = arsip_qs.filter(tanggal_upload__date__gte=tanggal_dari)
        except (ValueError, TypeError):
            pass
            
    if tanggal_sampai:
        try:
            arsip_qs = arsip_qs.filter(tanggal_upload__date__lte=tanggal_sampai)
        except (ValueError, TypeError):
            pass
            
    return arsip_qs, query, kategori_id, tanggal_dari, tanggal_sampai

@login_required
def arsip_laporan(request):
    arsip_qs, query, kategori_id, tanggal_dari, tanggal_sampai = _get_arsip_filtered_qs(request)
    kategori_aktif = Kategori.objects.filter(aktif=True)
    
    paginator = Paginator(arsip_qs, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
        
    context = {
        'page_obj': page_obj,
        'kategori_aktif': kategori_aktif,
        'query': query,
        'kategori_id': str(kategori_id),
        'tanggal_dari': tanggal_dari,
        'tanggal_sampai': tanggal_sampai,
        'total_arsip': arsip_qs.count()
    }
    return render(request, 'arsip/laporan.html', context)

@login_required
def arsip_export_csv(request):
    arsip_qs, _, _, _, _ = _get_arsip_filtered_qs(request)
    arsip_qs = arsip_qs.select_related('kategori', 'uploaded_by')
    
    now = timezone.localtime(timezone.now()) if getattr(settings, 'USE_TZ', False) else timezone.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="laporan_arsip_{timestamp}.csv"'
    
    # Write UTF-8 BOM for spreadsheet compatibility
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['No', 'Nama Warga', 'NIK', 'Kategori', 'Nama File', 'Keterangan', 'Uploaded By', 'Tanggal Upload', 'Google Drive ID'])

    def sanitize(val):
        if val and isinstance(val, str) and val.startswith(('=', '+', '-', '@')):
            return ' ' + val
        return val

    for idx, item in enumerate(arsip_qs, start=1):
        keterangan = item.keterangan if item.keterangan else ""
        uploaded_by = item.uploaded_by.username if item.uploaded_by else ""
        
        tanggal_upload = ""
        if item.tanggal_upload:
            local_dt = timezone.localtime(item.tanggal_upload) if getattr(settings, 'USE_TZ', False) else item.tanggal_upload
            tanggal_upload = local_dt.strftime('%Y-%m-%d %H:%M:%S')
            
        kategori_nama = item.kategori.nama if item.kategori else ""
        
        writer.writerow([
            idx,
            sanitize(item.nama_warga),
            sanitize(item.nik),
            sanitize(kategori_nama),
            sanitize(item.nama_file),
            sanitize(keterangan),
            sanitize(uploaded_by),
            tanggal_upload,
            sanitize(item.drive_file_id)
        ])
        
    AuditLog.objects.create(
        user=request.user,
        action="EXPORT_LAPORAN",
        description=f"User {request.user.username} melakukan export laporan Arsip CSV sejumlah {arsip_qs.count()} baris."
    )

    return response
