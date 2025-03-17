import requests
import re
import time
from .ssh_utils import remote_exec

def fetch_netdata(ip):
    try:
        url = f"http://{ip}:19999"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_netdata_version(ssh, password, use_sudo):
    """Cek versi Netdata yang terinstal."""
    out, _ = remote_exec(ssh, "command -v netdata && netdata -v || echo notfound", password, use_sudo)
    if "notfound" in out:
        return None  # Netdata tidak ditemukan
    return out.strip()

def get_netdata_major_version(version_output):
    """Ambil major version dari Netdata (misal 1.37.1-2 jadi 1.37.1)."""
    if not version_output:
        return None
    match = re.search(r"(\d+\.\d+\.\d+)", version_output)
    return match.group(1) if match else None

def wait_for_apt(ssh, password, use_sudo):
    """Tunggu proses APT selesai sebelum install/uninstall."""
    while True:
        out, _ = remote_exec(ssh, "pgrep -x apt || echo done", password, use_sudo)
        if "done" in out:
            break
        time.sleep(5)

def uninstall_netdata(ssh, password, use_sudo):
    """Uninstall Netdata dengan sudo kalau bukan root."""
    wait_for_apt(ssh, password, use_sudo)
    cmd = "apt purge -y netdata"
    if use_sudo:
        cmd = "sudo " + cmd
    return remote_exec(ssh, cmd, password, use_sudo)

def remove_netdata_source(ssh, password, use_sudo):
    """Cek dan hapus file /etc/apt/sources.list.d/netdata.sources jika ada."""
    check_cmd = "test -f /etc/apt/sources.list.d/netdata.sources && echo exists || echo notfound"
    out, _ = remote_exec(ssh, check_cmd, password, use_sudo)

    if "exists" in out:
        cmd = "rm -f /etc/apt/sources.list.d/netdata.sources"
        if use_sudo:
            cmd = "sudo " + cmd
        return remote_exec(ssh, cmd, password, use_sudo)
    return ("File netdata.sources tidak ditemukan.", "")

def install_netdata(ssh, password, use_sudo):
    """Install Netdata dengan sudo kalau bukan root."""
    wait_for_apt(ssh, password, use_sudo)
    cmd = "apt update && apt install -y netdata"
    if use_sudo:
        cmd = "sudo " + cmd
    return remote_exec(ssh, cmd, password, use_sudo)

def configure_netdata(ssh, password, use_sudo):
    """Konfigurasi Netdata agar bind socket ke IP 0.0.0.0."""
    config_file = "/etc/netdata/netdata.conf"

    # 🔍 Cek apakah file konfigurasi ada
    check_cmd = f"test -f {config_file} && echo exists || echo notfound"
    out, _ = remote_exec(ssh, check_cmd, password, use_sudo)

    if "notfound" in out:
        return ("File konfigurasi Netdata tidak ditemukan!", "")

    # 🛠️ Edit bagian bind socket to IP
    cmd = f"sed -i 's/^\\s*bind socket to IP = .*/        bind socket to IP = 0.0.0.0/' {config_file}"
    if use_sudo:
        cmd = "sudo " + cmd

    return remote_exec(ssh, cmd, password, use_sudo)

def restart_netdata(ssh, password, use_sudo):
    """Restart layanan Netdata hanya jika sudah terinstall."""
    check_cmd = "systemctl list-units --type=service | grep netdata || echo notfound"
    if use_sudo:
        check_cmd = "sudo " + check_cmd
    out, _ = remote_exec(ssh, check_cmd, password, use_sudo)

    if "notfound" in out:
        return ("Netdata service tidak ditemukan!", "")

    cmd = "systemctl restart netdata"
    if use_sudo:
        cmd = "sudo " + cmd
    return remote_exec(ssh, cmd, password, use_sudo)
