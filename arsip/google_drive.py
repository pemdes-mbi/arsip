import os
import base64
import requests
from django.conf import settings

def test_google_apps_script_connection():
    """
    Tests the GET connection to the Google Apps Script Web App.
    Returns True if successful, False otherwise.
    """
    url = getattr(settings, 'GOOGLE_APPS_SCRIPT_URL', None)
    if not url:
        raise ValueError("GOOGLE_APPS_SCRIPT_URL belum dikonfigurasi.")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('success') is True:
            return True
        else:
            raise Exception(data.get('message', 'Response success=false'))
    except Exception as e:
        raise Exception(f"Koneksi gagal: {str(e)}")

def upload_to_google_drive(file_path, kategori, nama_file, mime_type):
    """
    Uploads a local file to Google Drive via Apps Script Web App.
    """
    url = getattr(settings, 'GOOGLE_APPS_SCRIPT_URL', None)
    if not url:
        raise ValueError("GOOGLE_APPS_SCRIPT_URL belum dikonfigurasi.")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File tidak ditemukan: {file_path}")
        
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        payload = {
            "kategori": kategori,
            "nama_file": nama_file,
            "mime_type": mime_type,
            "file_base64": file_base64
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if data.get('success'):
            return {
                'file_id': data.get('file_id'),
                'folder_id': data.get('folder_id'),
                'folder_name': data.get('folder_name'),
                'url': data.get('url')
            }
        else:
            raise Exception(data.get('message', 'Gagal mengupload file ke Google Drive (success=false).'))
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP Request gagal: {str(e)}")
    except Exception as e:
        raise Exception(f"Upload error: {str(e)}")
