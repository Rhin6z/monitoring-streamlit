import streamlit as st
from Component.ssh_utils import connect_to_server
from Component.netdata_utils import (
    get_netdata_version, get_netdata_major_version, install_netdata,
    configure_netdata, restart_netdata, uninstall_netdata
)

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
        log_messages += uninstall_netdata(ssh, password, use_sudo)[0]
        log_messages += install_netdata(ssh, password, use_sudo)[0]

    st.info("⚙️ Mengkonfigurasi Netdata untuk bind ke 0.0.0.0...")
    log_messages += configure_netdata(ssh, password, use_sudo)[0]
    log_messages += restart_netdata(ssh, password, use_sudo)[0]

    # ✅ Simpan ke session state biar monitoring bisa jalan
    st.session_state.netdata_ready = True
    st.session_state.remote_ip = ip  

    ssh.close()
    return log_messages

# --- Streamlit UI ---
st.set_page_config(page_title="Remote Netdata Dashboard", layout="wide")
st.title("Remote Netdata Management")

tabs = st.tabs(["Auto Install & Configure", "Monitoring"])

with tabs[0]:
    st.header("Auto Install & Configure Netdata")
    remote_ip = st.text_input("Remote Server IP")
    username = st.text_input("Username", "root")
    password = st.text_input("Password", type="password")

    if st.button("Start Monitoring"):
        log_output = auto_install_and_configure(remote_ip, username, password)
        st.subheader("📜 Log Output:")
        st.code(log_output, language="bash")

with tabs[1]:
    st.header("📊 Monitoring Dashboard")

    if "netdata_ready" not in st.session_state or not st.session_state.netdata_ready:
        st.warning("Masukkan IP, Username, dan Password di tab pertama!")
    else:
        netdata_ip = st.session_state.remote_ip
        st.success(f"✅ Monitoring Netdata aktif di `{netdata_ip}`")

        # Baca isi HTML dari file
        with open("Component/netdata_dashboard.html", "r") as file:
            html_code = file.read()

        st.components.v1.html(html_code, height=700, scrolling=False)
