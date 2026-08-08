import json
import urllib.request
import urllib.error
import subprocess
import sys

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

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

def verify_api_key(api_key):
    """Verify that the API key is valid by making a test request to VirusTotal.
    Returns (True, None) on success or (False, error_message) on failure."""
    url = "https://www.virustotal.com/api/v3/users/me"
    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return True, None
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, "Authentication failed"
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)

def check_file_exists_vt(vt_path, sha256):
    """Check if the file hash already exists on VirusTotal using vt CLI."""
    try:
        cmd = [vt_path, 'file', sha256, '--format', 'json']
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=_NO_WINDOW
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

def get_user_quota(api_key):
    """Fetch user account info and overall API quota usage from VirusTotal API."""
    url = "https://www.virustotal.com/api/v3/users/me"
    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            data = res.get("data", {}).get("attributes", {})
            user_id = data.get("id") or data.get("username", "User")
            quotas = data.get("quotas", {})
            
            # Extract daily / monthly request quotas
            api_requests_daily = quotas.get("api_requests_daily", {})
            api_requests_monthly = quotas.get("api_requests_monthly", {})
            
            used_daily = api_requests_daily.get("user", {}).get("used", 0)
            allowed_daily = api_requests_daily.get("user", {}).get("allowed", 0)
            
            used_monthly = api_requests_monthly.get("user", {}).get("used", 0)
            allowed_monthly = api_requests_monthly.get("user", {}).get("allowed", 0)
            
            user_group = data.get("user_group", {}).get("id", "standard")
            
            return {
                "user_id": user_id,
                "user_group": user_group,
                "daily_used": used_daily,
                "daily_allowed": allowed_daily,
                "monthly_used": used_monthly,
                "monthly_allowed": allowed_monthly
            }
    except Exception:
        return None

def reanalyze_item(item_type, item_id, api_key, vt_path=None):
    """Request a fresh re-analysis for a file, domain, IP, or URL."""
    if item_type == "file":
        url = f"https://www.virustotal.com/api/v3/files/{item_id}/analyse"
    elif item_type == "domain":
        url = f"https://www.virustotal.com/api/v3/domains/{item_id}/analyse"
    elif item_type == "ip":
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{item_id}/analyse"
    elif item_type == "url":
        url = f"https://www.virustotal.com/api/v3/urls/{item_id}/analyse"
    else:
        raise ValueError(f"Unsupported item type for re-analysis: {item_type}")

    req = urllib.request.Request(
        url,
        data=b"",
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            analysis_id = data.get("data", {}).get("id")
            return analysis_id
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise ValueError("api_key_invalid_err")
        raise ValueError(f"HTTP {e.code}: {e.reason}")
    except Exception as ex:
        raise ex

def submit_url_scan(url_str, api_key):
    """Submit a URL for a live scan on VirusTotal. Returns analysis_id."""
    import urllib.parse
    url = "https://www.virustotal.com/api/v3/urls"
    data = f"url={urllib.parse.quote(url_str, safe='')}".encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "x-apikey": api_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            analysis_id = res.get("data", {}).get("id")
            return analysis_id
    except Exception as ex:
        raise ex

def get_file_behaviours(sha256, api_key):
    """Fetch file execution behaviors and sandbox reports from VirusTotal API."""
    url = f"https://www.virustotal.com/api/v3/files/{sha256}/behaviours"
    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("data", [])
    except Exception:
        return []

def get_subdomains(domain, api_key):
    """Fetch subdomains for a given domain from VirusTotal API."""
    url = f"https://www.virustotal.com/api/v3/domains/{domain}/subdomains?limit=20"
    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("data", [])
    except Exception:
        return []

def get_dns_resolutions(item_type, item_id, api_key):
    """Fetch historical DNS resolutions for a domain or IP from VirusTotal API."""
    if item_type == "domain":
        url = f"https://www.virustotal.com/api/v3/domains/{item_id}/resolutions?limit=20"
    else:
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{item_id}/resolutions?limit=20"

    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("data", [])
    except Exception:
        return []

def get_comments(collection, item_id, api_key):
    """Fetch community comments for a file, domain, IP, or URL."""
    url = f"https://www.virustotal.com/api/v3/{collection}/{item_id}/comments?limit=10"
    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("data", [])
    except Exception:
        return []

def add_comment(collection, item_id, text, api_key):
    """Post a comment to a file, domain, IP, or URL on VirusTotal."""
    url = f"https://www.virustotal.com/api/v3/{collection}/{item_id}/comments"
    payload = json.dumps({
        "data": {
            "type": "comment",
            "attributes": {
                "text": text
            }
        }
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "x-apikey": api_key,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as ex:
        raise ex

def delete_comment(comment_id, api_key):
    """Delete a comment by its ID on VirusTotal."""
    url = f"https://www.virustotal.com/api/v3/comments/{comment_id}"
    req = urllib.request.Request(
        url,
        headers={
            "x-apikey": api_key,
            "User-Agent": "Mozilla/5.0"
        },
        method="DELETE"
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_bytes = response.read()
            if res_bytes:
                return json.loads(res_bytes.decode('utf-8'))
            return {"data": "deleted"}
    except Exception as ex:
        raise ex

def vote_item(collection, item_id, verdict, api_key):
    """Submit a vote ('harmless' or 'malicious') for an item on VirusTotal."""
    url = f"https://www.virustotal.com/api/v3/{collection}/{item_id}/votes"
    payload = json.dumps({
        "data": {
            "type": "vote",
            "attributes": {
                "verdict": verdict
            }
        }
    }).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "x-apikey": api_key,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as ex:
        try:
            err_body = ex.read().decode('utf-8')
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message", str(ex))
            raise ValueError(msg)
        except Exception:
            raise ex
    except Exception as ex:
        raise ex

def get_user_vote(collection, item_id, api_key):
    """Fetch current user's vote for an item ('harmless', 'malicious', or None)."""
    url = f"https://www.virustotal.com/api/v3/{collection}/{item_id}/user_votes"
    req = urllib.request.Request(
        url,
        headers={
            "x-apikey": api_key,
            "User-Agent": "Mozilla/5.0"
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            votes = data.get("data", [])
            if votes and isinstance(votes, list):
                first_vote = votes[0]
                return first_vote.get("attributes", {}).get("verdict")
    except Exception:
        pass
    return None

def diff_files(hash1, hash2, vt_path):
    """Compare two file hashes using vt CLI `vt diff` or fetch both file details."""
    try:
        cmd = [vt_path, 'diff', hash1, hash2, '--format', 'json']
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=_NO_WINDOW
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return json.loads(proc.stdout)
    except Exception:
        pass
    return None

def get_yara_rulesets(api_key):
    """Fetch user's YARA Livehunt rulesets directly via VirusTotal API v3."""
    url = "https://www.virustotal.com/api/v3/yara_rulesets?limit=20"
    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("data", [])
    except urllib.error.HTTPError as ex:
        if ex.code == 403:
            raise PermissionError("YARA Livehunt requires a VirusTotal Premium API key.")
        raise ex
    except Exception as ex:
        raise ex


