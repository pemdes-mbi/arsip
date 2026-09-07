import os
from django import forms
from django.core.exceptions import ValidationError
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
        self.fields['kategori'].queryset = Kategori.objects.filter(aktif=True)
        self.fields['nik'].required = True
        if not self.instance.pk:
            self.fields['file'].required = True
        else:
            self.fields['file'].required = False

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv']
            if ext not in valid_extensions:
                raise ValidationError('Hanya file gambar (JPG/PNG) atau dokumen (PDF/Word/Excel/CSV) yang diperbolehkan.')
            if file.size > 10 * 1024 * 1024: # 10MB
                raise ValidationError('Ukuran file maksimal adalah 10MB.')
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
