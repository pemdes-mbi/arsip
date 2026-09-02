from django.urls import path
from . import views

app_name = 'arsip'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('kategori/', views.kategori_list, name='kategori_list'),
    path('kategori/tambah/', views.kategori_tambah, name='kategori_tambah'),
    path('kategori/<int:id>/edit/', views.kategori_edit, name='kategori_edit'),
    path('kategori/<int:id>/toggle/', views.kategori_toggle, name='kategori_toggle'),
    path('arsip/', views.arsip_list, name='arsip_list'),
    path('arsip/tambah/', views.arsip_tambah, name='arsip_tambah'),
    path('arsip/<int:id>/', views.arsip_detail, name='arsip_detail'),
    path('arsip/<int:id>/edit/', views.arsip_edit, name='arsip_edit'),
    path('arsip/<int:id>/hapus/', views.arsip_hapus, name='arsip_hapus'),
]
