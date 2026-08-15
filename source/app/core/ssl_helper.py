import os
import sys
import ssl


def get_ca_bundle_path():
    """
    Locates a valid CA certificate bundle file across various operating systems
    and Linux distributions (Fedora/RHEL, Ubuntu/Debian, Arch, openSUSE, Alpine, etc.).
    """
    # 1. Check existing environment variables
    for env_var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        val = os.environ.get(env_var)
        if val and os.path.exists(val):
            return val

    # 2. Check certifi bundle (included in Python environment or PyInstaller bundle)
    try:
        import certifi
        cert_path = certifi.where()
        if cert_path and os.path.exists(cert_path):
            return cert_path
    except Exception:
        pass

    # 3. Check PyInstaller _MEIPASS directory for bundled cacert.pem
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled_cert = os.path.join(sys._MEIPASS, "certifi", "cacert.pem")
        if os.path.exists(bundled_cert):
            return bundled_cert

    # 4. Standard Linux / Unix CA certificate paths
    system_paths = [
        "/etc/pki/tls/certs/ca-bundle.crt",                   # Fedora, RHEL, CentOS
        "/etc/ssl/certs/ca-certificates.crt",               # Debian, Ubuntu, Arch, Gentoo
        "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem", # Fedora, RHEL 7+
        "/etc/ssl/ca-bundle.pem",                           # openSUSE
        "/etc/ssl/cert.pem",                                # Alpine, macOS, OpenBSD
        "/etc/pki/tls/cert.pem",                            # Fedora alternative
        "/usr/local/share/certs/ca-root-nss.crt",           # FreeBSD
    ]
    for p in system_paths:
        if os.path.exists(p):
            return p

    return None


def get_ssl_context():
    """
    Creates an SSLContext configured with the best available CA certificate bundle.
    """
    ca_path = get_ca_bundle_path()
    if ca_path:
        try:
            return ssl.create_default_context(cafile=ca_path)
        except Exception:
            pass
    return ssl.create_default_context()


def init_ssl_context():
    """
    Globally initializes SSL certificate paths in environment variables and sets
    ssl._create_default_https_context so that all standard library HTTPS calls
    (urllib.request, urllib3, etc.) find the appropriate root certificates.
    """
    ca_path = get_ca_bundle_path()
    if ca_path:
        os.environ["SSL_CERT_FILE"] = ca_path
        os.environ["REQUESTS_CA_BUNDLE"] = ca_path
        try:
            ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=ca_path)
        except Exception:
            pass
