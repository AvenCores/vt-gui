import json
import uuid
import mimetypes
import urllib.request
import urllib.error
import subprocess
import os

class ProgressFileWrapper:
    """Wrapper around a file-like object to track read progress during upload."""
    def __init__(self, header_bytes, file_path, footer_bytes, progress_callback=None):
        self.header = header_bytes
        self.file_path = file_path
        self.footer = footer_bytes
        self.file_size = os.path.getsize(file_path)
        self.total_size = len(header_bytes) + self.file_size + len(footer_bytes)
        self.bytes_read = 0
        self.progress_callback = progress_callback
        self.file_obj = open(file_path, "rb")
        
    def read(self, size=-1):
        data = b""
        if len(self.header) > 0:
            if size < 0 or size >= len(self.header):
                data += self.header
                self.bytes_read += len(self.header)
                self.header = b""
            else:
                chunk = self.header[:size]
                data += chunk
                self.header = self.header[size:]
                self.bytes_read += len(chunk)
                if self.progress_callback:
                    self.progress_callback(self.bytes_read, self.total_size)
                return data
                
        if len(data) < size or size < 0:
            remaining = size - len(data) if size >= 0 else -1
            file_data = self.file_obj.read(remaining)
            if file_data:
                data += file_data
                self.bytes_read += len(file_data)
                if self.progress_callback:
                    self.progress_callback(self.bytes_read, self.total_size)
            else:
                if len(self.footer) > 0:
                    remaining = size - len(data) if size >= 0 else -1
                    if remaining < 0 or remaining >= len(self.footer):
                        data += self.footer
                        self.bytes_read += len(self.footer)
                        self.footer = b""
                    else:
                        chunk = self.footer[:remaining]
                        data += chunk
                        self.bytes_read += len(chunk)
                        self.footer = self.footer[remaining:]
                        
        if self.progress_callback:
            self.progress_callback(self.bytes_read, self.total_size)
        return data
        
    def close(self):
        self.file_obj.close()
        
    def __len__(self):
        return self.total_size

def get_large_file_upload_url(api_key):
    """Request a large file upload URL from VirusTotal V3 API."""
    url = "https://www.virustotal.com/api/v3/files/upload_url"
    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("data")
    except Exception:
        return "https://www.virustotal.com/api/v3/files"

def check_file_exists_direct(sha256, api_key):
    """Check if the file hash already exists on VirusTotal using HTTP API."""
    url = f"https://www.virustotal.com/api/v3/files/{sha256}"
    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code in (401, 403):
            raise ValueError("api_key_invalid_err")
        raise e
    except Exception:
        return None

def upload_file_direct(file_path, api_key, progress_callback=None):
    """Upload a file directly to VirusTotal using HTTP multipart/form-data."""
    file_size = os.path.getsize(file_path)
    
    if file_size > 32 * 1024 * 1024:
        upload_url = get_large_file_upload_url(api_key)
    else:
        upload_url = "https://www.virustotal.com/api/v3/files"
        
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    filename = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
        
    part_boundary = f"--{boundary}\r\n".encode('utf-8')
    part_header = (
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: {mime_type}\r\n\r\n'
    ).encode('utf-8')
    part_footer = f"\r\n--{boundary}--\r\n".encode('utf-8')
    
    header_bytes = part_boundary + part_header
    footer_bytes = part_footer
    
    wrapper = ProgressFileWrapper(
        header_bytes=header_bytes,
        file_path=file_path,
        footer_bytes=footer_bytes,
        progress_callback=progress_callback
    )
    
    req = urllib.request.Request(
        upload_url,
        data=wrapper,
        headers={
            "x-apikey": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(wrapper.total_size),
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    finally:
        wrapper.close()

def check_analysis_status_direct(analysis_id, api_key):
    """Retrieve analysis status using HTTP API."""
    url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise ValueError("api_key_invalid_err")
        raise e

def check_file_exists_vt(vt_path, sha256):
    """Check if the file hash already exists on VirusTotal using vt.exe CLI."""
    try:
        cmd = [vt_path, 'file', sha256, '--format', 'json']
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict):
                return data
    except Exception:
        pass
    return None
