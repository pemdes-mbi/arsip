from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Kategori, Arsip
from .forms import KategoriForm, ArsipForm

@login_required
def dashboard(request):
    total_arsip = Arsip.objects.count()
    total_kategori = Kategori.objects.count()
    kategori_aktif = Kategori.objects.filter(aktif=True).count()
    kategori_nonaktif = Kategori.objects.filter(aktif=False).count()
    arsip_terbaru = Arsip.objects.all().order_by('-tanggal_upload')[:5]
    
    return render(request, 'dashboard/index.html', {
        'total_arsip': total_arsip,
        'total_kategori': total_kategori,
        'kategori_aktif': kategori_aktif,
        'kategori_nonaktif': kategori_nonaktif,
        'arsip_terbaru': arsip_terbaru
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

@login_required
def arsip_list(request):
    query = request.GET.get('q', '')
    kategori_id = request.GET.get('kategori', '')
    
    arsip_qs = Arsip.objects.all().order_by('-tanggal_upload')
    
    if query:
        arsip_qs = arsip_qs.filter(
            Q(nama_warga__icontains=query) |
            Q(nik__icontains=query) |
            Q(nama_file__icontains=query)
        )
        
    if kategori_id:
        arsip_qs = arsip_qs.filter(kategori_id=kategori_id)
        
    kategori_aktif = Kategori.objects.filter(aktif=True)
    
    return render(request, 'arsip/daftar.html', {
        'arsip_list': arsip_qs,
        'query': query,
        'kategori_id': str(kategori_id),
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
                
            return redirect('arsip:arsip_list')
    else:
        form = ArsipForm()
    
    return render(request, 'arsip/tambah.html', {'form': form})

@login_required
def arsip_detail(request, id):
    arsip = get_object_or_404(Arsip, pk=id)
    
    file_type = None
    if arsip.file:
        import os
        ext = os.path.splitext(arsip.file.name)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png']:
            file_type = 'image'
        elif ext == '.pdf':
            file_type = 'pdf'
        else:
            file_type = 'unsupported'
            
    return render(request, 'arsip/detail.html', {
        'arsip': arsip,
        'file_type': file_type
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
    arsip.delete()
    
    messages.success(request, 'Arsip berhasil dihapus dari sistem.')
    return redirect('arsip:arsip_list')

