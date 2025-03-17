import streamlit as st
from Component.ssh_utils import connect_to_server
from Component.netdata_utils import (
    get_netdata_version, get_netdata_major_version, install_netdata,
    configure_netdata, restart_netdata, uninstall_netdata, remove_netdata_source
)

# Import komponen terminal
from terminal_component import create_terminal_component

def auto_install_and_configure(ip, username, password):
    log_messages = ""
    use_sudo = username.lower() != "root"

    ssh = connect_to_server(ip, username, password)
    if ssh is None:
        return "Gagal terhubung ke server."

    st.write(f"Terhubung ke {ip} sebagai {username}")

    version_output = get_netdata_version(ssh, password, use_sudo)
    major_version = get_netdata_major_version(version_output)

    if major_version and major_version < "1.38.0":
        st.success(f"✅ Netdata sudah terinstal dengan versi {major_version}. Lanjut konfigurasi.")
        log_messages += f"✅ Netdata versi {major_version} sudah sesuai.\n"
    else:
        st.warning(f"⚠️ Netdata versi {major_version} harus dihapus dan diinstall ulang.")
        log_messages += f"⚠️ Netdata versi {major_version} harus diinstall ulang.\n"

        # 🔥 Uninstall Netdata
        out, err = uninstall_netdata(ssh, password, use_sudo)
        log_messages += "=== Uninstall Netdata ===\n" + out + err + "\n"

        # 🔍 Cek & hapus file sources.list.d/netdata.sources kalau ada
        st.info("🔍 Mengecek file /etc/apt/sources.list.d/netdata.sources...")
        out, err = remove_netdata_source(ssh, password, use_sudo)
        log_messages += "=== Hapus netdata.sources ===\n" + out + err + "\n"

        # 🛠️ Install ulang Netdata
        st.info("🛠️ Menginstal Netdata...")
        out, err = install_netdata(ssh, password, use_sudo)
        log_messages += "=== Install Netdata ===\n" + out + err + "\n"

        # ✅ Cek apakah Netdata berhasil diinstall
        version_output = get_netdata_version(ssh, password, use_sudo)
        if not version_output:
            st.error("❌ Gagal menginstall Netdata!")
            ssh.close()
            return log_messages

    # ⚙️ Konfigurasi Netdata
    st.info("⚙️ Mengkonfigurasi Netdata untuk bind ke 0.0.0.0...")
    out, err = configure_netdata(ssh, password, use_sudo)
    log_messages += "=== Konfigurasi netdata.conf ===\n" + out + err + "\n"

    # 🚀 Restart Netdata jika berhasil diinstall
    st.info("🔄 Merestart layanan Netdata...")
    out, err = restart_netdata(ssh, password, use_sudo)
    log_messages += "=== Restart Netdata ===\n" + out + err + "\n"

    # ✅ Simpan ke session state biar monitoring bisa jalan
    st.session_state.netdata_ready = True
    st.session_state.remote_ip = ip
    st.session_state.username = username  # Simpan username untuk terminal
    st.session_state.password = password  # Simpan password untuk terminal

    ssh.close()
    return log_messages

# --- Streamlit UI ---
st.set_page_config(page_title="Remote Netdata Dashboard", layout="wide")
st.title("Remote Netdata Management")

with st.sidebar:
    st.header("Auto Install & Configure Netdata")
    remote_ip = st.text_input("Remote Server IP")
    username = st.text_input("Username", "root")
    password = st.text_input("Password", type="password")

    if st.button("Start Monitoring"):
        log_output = auto_install_and_configure(remote_ip, username, password)
        with st.expander("Log Output"):
            st.code(log_output, language="bash")

# Buat tabs untuk dashboard dan terminal
tab1, tab2 = st.tabs(["📊 Monitoring Dashboard", "💻 Terminal"])

with tab1:
    st.header("📊 Monitoring Dashboard")
    
    if "netdata_ready" not in st.session_state or not st.session_state.netdata_ready:
        st.warning("Masukkan IP, Username, dan Password di side bar!")
    else:
        netdata_ip = st.session_state['remote_ip']
        st.success(f"✅ Monitoring Netdata active at `{netdata_ip}`")

        html_code = f'<iframe src="http://{netdata_ip}:19999" width="100%" height="1000"></iframe>'
        st.components.v1.html(html_code, height=1000, scrolling=False)

with tab2:
    # Tampilkan komponen terminal
    create_terminal_component()