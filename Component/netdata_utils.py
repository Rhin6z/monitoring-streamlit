import requests
import re
from .ssh_utils import remote_exec

def fetch_netdata(ip):
    """Cek apakah Netdata berjalan dengan API `/api/v1/info`."""
    try:
        url = f"http://{ip}:19999/api/v1/info"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_netdata_version(ssh, password, use_sudo):
    """Cek versi Netdata yang terinstal."""
    out, _ = remote_exec(ssh, "netdata -v", password, use_sudo)
    return out.strip()

def get_netdata_major_version(version_output):
    """Ambil major version dari Netdata (misal 1.37.1-2 jadi 1.37.1)."""
    match = re.search(r"(\d+\.\d+\.\d+)", version_output)
    return match.group(1) if match else None

def uninstall_netdata(ssh, password, use_sudo):
    """Uninstall Netdata."""
    return remote_exec(ssh, "apt purge -y netdata", password, use_sudo)

def install_netdata(ssh, password, use_sudo):
    """Install Netdata menggunakan apt install."""
    return remote_exec(ssh, "apt update && apt install -y netdata", password, use_sudo)

def configure_netdata(ssh, password, use_sudo):
    """Konfigurasi Netdata agar bind socket ke IP 0.0.0.0."""
    config_file = "/etc/netdata/netdata.conf"
    cmd = f"sed -i '/\\[web\\]/, /^\\[/ s/^\\s*bind to.*/    bind to = 0.0.0.0/' {config_file}"
    return remote_exec(ssh, cmd, password, use_sudo)

def restart_netdata(ssh, password, use_sudo):
    """Restart layanan Netdata."""
    return remote_exec(ssh, "systemctl restart netdata", password, use_sudo)
