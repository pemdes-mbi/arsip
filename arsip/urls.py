from django.urls import path
from . import views

app_name = 'arsip'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('kategori/', views.kategori_list, name='kategori_list'),
    path('kategori/tambah/', views.kategori_tambah, name='kategori_tambah'),
    path('kategori/<int:id>/edit/', views.kategori_edit, name='kategori_edit'),
    path('kategori/<int:id>/toggle/', views.kategori_toggle, name='kategori_toggle'),
    path('kategori/<int:id>/hapus/', views.kategori_hapus, name='kategori_hapus'),
    path('arsip/', views.arsip_list, name='arsip_list'),
    path('arsip/tambah/', views.arsip_tambah, name='arsip_tambah'),
    path('arsip/<int:id>/', views.arsip_detail, name='arsip_detail'),
    path('arsip/<int:id>/edit/', views.arsip_edit, name='arsip_edit'),
    path('arsip/<int:id>/hapus/', views.arsip_hapus, name='arsip_hapus'),
    
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/tambah/', views.user_add, name='user_add'),
    path('users/<int:id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:id>/toggle/', views.user_toggle, name='user_toggle'),
    
    # Audit Log
    path('audit-log/', views.audit_log, name='audit_log'),
    # Laporan & Export
    path('laporan/', views.arsip_laporan, name='arsip_laporan'),
    path('export/csv/', views.arsip_export_csv, name='arsip_export_csv'),
]
