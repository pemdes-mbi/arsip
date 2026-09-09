import os
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from .models import Kategori, Arsip

class KategoriForm(forms.ModelForm):
    class Meta:
        model = Kategori
        fields = ['nama']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan nama kategori'})
        }

    def clean_nama(self):
        nama = self.cleaned_data.get('nama')
        qs = Kategori.objects.filter(nama__iexact=nama)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Kategori dengan nama ini sudah ada.')
        return nama

class ArsipForm(forms.ModelForm):
    class Meta:
        model = Arsip
        fields = ['nama_warga', 'nik', 'kategori', 'nama_file', 'keterangan', 'file']
        widgets = {
            'nama_warga': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Warga'}),
            'nik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NIK', 'maxlength': '16'}),
            'kategori': forms.Select(attrs={'class': 'form-select'}),
            'nama_file': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama File'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Keterangan...'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png,.pdf'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.kategori:
            self.fields['kategori'].queryset = Kategori.objects.filter(aktif=True) | Kategori.objects.filter(pk=self.instance.kategori.pk)
        else:
            self.fields['kategori'].queryset = Kategori.objects.filter(aktif=True)
            
        self.fields['nik'].required = True
        if not self.instance.pk:
            self.fields['file'].required = True
        else:
            self.fields['file'].required = False

    def clean_kategori(self):
        kategori = self.cleaned_data.get('kategori')
        if not kategori:
            raise ValidationError('Kategori surat wajib dipilih.')
        
        if not self.instance.pk:
            # Form Tambah (Arsip Baru): Hanya kategori Master Resmi Aktif yang diizinkan
            if not kategori.aktif:
                raise ValidationError('Kategori legacy/nonaktif tidak dapat digunakan untuk arsip baru. Pilih Master Kategori Resmi.')
        else:
            # Form Edit: Kategori existing boleh dipertahankan (meskipun legacy)
            # Namun jika diubah ke kategori lain, kategori tujuan harus aktif
            if kategori.pk != self.instance.kategori_id and not kategori.aktif:
                raise ValidationError('Tidak dapat mengubah ke kategori legacy/nonaktif. Pilih Master Kategori Resmi yang aktif.')
                
        return kategori

    def clean_nik(self):
        nik = self.cleaned_data.get('nik', '').strip()
        if not nik:
            raise ValidationError('Nomor Induk Kependudukan (NIK) wajib diisi.')
        
        # Jika arsip existing dan NIK tidak diubah, izinkan format lama (legacy) tetap utuh
        if self.instance and self.instance.pk and nik == self.instance.nik:
            return nik

        # Untuk data baru atau jika NIK diubah: wajib 16 digit angka
        if not nik.isdigit():
            raise ValidationError('NIK hanya boleh terdiri dari digit angka (0-9).')
        if len(nik) != 16:
            raise ValidationError('NIK harus tepat 16 digit angka.')
            
        return nik

    def clean_nama_warga(self):
        nama = self.cleaned_data.get('nama_warga', '').strip()
        if not nama:
            raise ValidationError('Nama warga wajib diisi.')
        if len(nama) > 150:
            raise ValidationError('Nama warga maksimal 150 karakter.')
        return nama

    def clean_nama_file(self):
        nama_file = self.cleaned_data.get('nama_file', '').strip()
        if not nama_file:
            raise ValidationError('Judul / nama dokumen wajib diisi.')
        if len(nama_file) > 255:
            raise ValidationError('Judul / nama dokumen maksimal 255 karakter.')
        # Path traversal protection
        if '..' in nama_file or '/' in nama_file or '\\' in nama_file:
            raise ValidationError('Judul dokumen tidak boleh mengandung karakter path traversal (../, /, \\).')
        return nama_file

    def clean_keterangan(self):
        keterangan = self.cleaned_data.get('keterangan', '')
        if keterangan:
            keterangan = keterangan.strip()
        return keterangan

    def clean_file(self):
        file = self.cleaned_data.get('file')
        # Hanya jalankan validasi mendalam jika user mengunggah file baru (UploadedFile)
        # Jangan memvalidasi ulang FieldFile existing saat Edit jika tidak ada file baru diunggah
        if file and isinstance(file, UploadedFile):
            # 1. Reject empty file (0 byte)
            if file.size == 0:
                raise ValidationError('File tidak boleh kosong (0 byte).')

            # 2. File size limit validation
            from django.conf import settings
            max_size_mb = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 10)
            max_size_bytes = max_size_mb * 1024 * 1024
            if file.size > max_size_bytes:
                raise ValidationError(f'Ukuran file melebihi batas maksimal ({max_size_mb}MB).')

            # 3. Path traversal & filename safety
            raw_filename = file.name or ''
            if '..' in raw_filename or '/' in raw_filename or '\\' in raw_filename:
                raise ValidationError('Nama file tidak valid atau mengandung path traversal (../, /, \\).')
            
            basename = os.path.basename(raw_filename).strip()
            if not basename:
                raise ValidationError('Nama file tidak valid.')

            # 4. Extension & double extension validation (case-insensitive)
            parts = [p.lower() for p in basename.split('.') if p]
            if len(parts) < 2:
                raise ValidationError('File harus memiliki ekstensi yang valid.')

            ext = f".{parts[-1]}"
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            dangerous_extensions = {
                'exe', 'bat', 'cmd', 'sh', 'ps1', 'php', 'phtml', 'py', 'js',
                'dll', 'msi', 'scr', 'vbs', 'html', 'htm', 'svg', 'cgi', 'asp',
                'aspx', 'jsp', 'jar', 'war', 'com', 'bin'
            }

            # Executable & script protection
            if parts[-1] in dangerous_extensions:
                raise ValidationError('File executable / script berbahaya tidak diperbolehkan.')

            if ext not in valid_extensions:
                raise ValidationError('Tipe file tidak diizinkan. Hanya file PDF, JPG, JPEG, dan PNG yang diperbolehkan.')

            # Double extension protection
            if len(parts) > 2:
                for mid_part in parts[1:-1]:
                    if mid_part in dangerous_extensions:
                        raise ValidationError('Nama file mengandung ekstensi ganda berbahaya (double extension).')

            # 5. Content & Magic Bytes / Signature validation
            try:
                header = file.read(16)
                file.seek(0)  # Reset pointer so subsequent reads work

                if ext == '.pdf':
                    if not header.startswith(b'%PDF'):
                        raise ValidationError('Isi file tidak sesuai dengan format PDF (Magic bytes tidak valid).')
                elif ext in ['.jpg', '.jpeg']:
                    if not header.startswith(b'\xff\xd8'):
                        raise ValidationError('Isi file tidak sesuai dengan format JPG/JPEG (Magic bytes tidak valid).')
                    try:
                        from PIL import Image
                        img = Image.open(file)
                        img.verify()
                        file.seek(0)
                        if img.format not in ['JPEG', 'MPO']:
                            raise ValidationError('Format gambar bukan JPEG yang valid.')
                    except ValidationError:
                        raise
                    except Exception:
                        raise ValidationError('File gambar JPG/JPEG rusak atau format tidak valid.')
                elif ext == '.png':
                    if not header.startswith(b'\x89PNG\r\n\x1a\n'):
                        raise ValidationError('Isi file tidak sesuai dengan format PNG (Magic bytes tidak valid).')
                    try:
                        from PIL import Image
                        img = Image.open(file)
                        img.verify()
                        file.seek(0)
                        if img.format != 'PNG':
                            raise ValidationError('Format gambar bukan PNG yang valid.')
                    except ValidationError:
                        raise
                    except Exception:
                        raise ValidationError('File gambar PNG rusak atau format tidak valid.')
            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError(f'Gagal memvalidasi isi file: {str(e)}')

            # Update the file name to the safe basename
            file.name = basename

        return file


from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class UserAddForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Konfirmasi Password'}), label='Konfirmasi Password')
    role = forms.ChoiceField(choices=[('admin', 'Admin'), ('user', 'User Biasa')], widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Depan'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Belakang'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords tidak cocok.')
        return cleaned_data

class UserEditForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Biarkan kosong jika tidak diubah'}), required=False, help_text='Kosongkan jika tidak ingin mengubah password.')
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Konfirmasi Password'}), required=False, label='Konfirmasi Password')
    role = forms.ChoiceField(choices=[('admin', 'Admin'), ('user', 'User Biasa')], widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['role'] = 'admin' if self.instance.is_superuser else 'user'

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password, self.instance)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password or password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Passwords tidak cocok.')
        return cleaned_data
