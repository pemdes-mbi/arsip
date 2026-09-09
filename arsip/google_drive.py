import os
import base64
import logging
import requests
from django.conf import settings

logger = logging.getLogger('arsip.google_drive')

def test_google_apps_script_connection():
    """
    Tests the GET connection to the Google Apps Script Web App.
    Returns True if successful, False otherwise.
    """
    url = getattr(settings, 'GOOGLE_APPS_SCRIPT_URL', None)
    if not url:
        logger.error("GOOGLE_APPS_SCRIPT_URL is not configured.")
        raise ValueError("GOOGLE_APPS_SCRIPT_URL belum dikonfigurasi.")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('success') is True:
            logger.info("Google Apps Script connection test succeeded.")
            return True
        else:
            msg = data.get('message', 'Response success=false')
            logger.warning("Google Apps Script connection test returned success=false.")
            raise Exception(msg)
    except requests.exceptions.Timeout:
        logger.error("Google Apps Script connection test timed out.")
        raise Exception("Koneksi timeout.")
    except requests.exceptions.ConnectionError:
        logger.error("Google Apps Script connection test network error.")
        raise Exception("Koneksi gagal terhubung.")
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', 'unknown')
        logger.error("Google Apps Script connection test HTTP error (status %s).", status)
        raise Exception(f"HTTP error status: {status}")
    except requests.exceptions.RequestException:
        logger.error("Google Apps Script connection test request error.")
        raise Exception("Request gagal.")
    except Exception as e:
        logger.error("Google Apps Script connection test unexpected error: %s", type(e).__name__)
        raise Exception(f"Koneksi gagal: {str(e)}")

def upload_to_google_drive(file_path, kategori, nama_file, mime_type):
    """
    Uploads a local file to Google Drive via Apps Script Web App.
    """
    url = getattr(settings, 'GOOGLE_APPS_SCRIPT_URL', None)
    if not url:
        logger.error("GOOGLE_APPS_SCRIPT_URL is not configured.")
        raise ValueError("GOOGLE_APPS_SCRIPT_URL belum dikonfigurasi.")
    
    if not os.path.exists(file_path):
        logger.error("File for Google Drive upload does not exist at specified path.")
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
        
        logger.info("Uploading file to Google Drive via Apps Script (file: %s, mime: %s).", nama_file, mime_type)
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if data.get('success'):
            logger.info("Google Drive upload successful for file: %s.", nama_file)
            return {
                'file_id': data.get('file_id'),
                'folder_id': data.get('folder_id'),
                'folder_name': data.get('folder_name'),
                'url': data.get('url')
            }
        else:
            msg = data.get('message', 'Gagal mengupload file ke Google Drive (success=false).')
            logger.warning("Google Apps Script returned success=false during upload.")
            raise Exception(msg)
            
    except requests.exceptions.Timeout:
        logger.error("Google Drive upload timed out after 30 seconds.")
        raise Exception("Koneksi Google Apps Script timeout.")
    except requests.exceptions.ConnectionError:
        logger.error("Google Drive upload network connection error.")
        raise Exception("Gagal terhubung ke Google Apps Script.")
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', 'unknown')
        logger.error("Google Drive upload HTTP error (status %s).", status)
        raise Exception(f"HTTP error status: {status}")
    except requests.exceptions.RequestException:
        logger.error("Google Drive upload request error.")
        raise Exception("Request ke Google Apps Script gagal.")
    except Exception as e:
        logger.error("Google Drive upload encountered unexpected error: %s", type(e).__name__)
        raise Exception(f"Upload error: {str(e)}")

