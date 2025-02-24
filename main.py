import streamlit as st
from Component.ssh_utils import connect_to_server
from Component.netdata_utils import (
    get_netdata_version, get_netdata_major_version, install_netdata,
    configure_netdata, restart_netdata, uninstall_netdata, remove_netdata_source
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

        # 🔥 Buat HTML secara langsung dengan IP user
        html_code = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <script type="text/javascript" src="http://{netdata_ip}:19999/dashboard.js"></script>
            <script>
            var netdataTheme = 'slate';
            var netdataPrepCallback = function() {{
                NETDATA.requiredCSS = [];
            }};
            </script>
            <style>
                body {{
                    background: transparent !important;
                }}
                .wrap {{
                    max-width: 1280px;
                    margin: 0 auto;
                }}
                h3 {{
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .charts {{
                    display: flex;
                    flex-flow: row wrap;
                    justify-content: space-around;
                }}
                .charts > div {{
                    margin-bottom: 6rem;
                    position: relative;
                }}
                .netdata-chart-row * {{ color: #ffffff !important; }}
            </style>
        </head>
        <body>
            <div class="netdata-chart-row">
                <div class="netdata-container-easypiechart" style="margin-right: 10px; width: 9%;" data-netdata="system.swap" data-dimensions="used" data-append-options="percentage" data-chart-library="easypiechart" data-title="Used Swap" data-units="%" data-easypiechart-max-value="100" data-width="9%" data-points="300" data-colors="#DD4400"></div>

                <div class="netdata-container-easypiechart" style="margin-right: 10px; width: 11%;" data-netdata="system.io" data-dimensions="in" data-chart-library="easypiechart" data-title="Disk Read" data-width="11%" data-points="300" data-common-units="system.io.mainhead"></div>

                <div class="netdata-container-easypiechart" style="margin-right: 10px; width: 11%;" data-netdata="system.io" data-dimensions="out" data-chart-library="easypiechart" data-title="Disk Write" data-width="11%" data-points="300" data-common-units="system.io.mainhead"></div>

                <div class="netdata-container-gauge" style="margin-right: 10px; width: 20%;" data-netdata="system.cpu" data-chart-library="gauge" data-title="CPU" data-units="%" data-gauge-max-value="100" data-width="20%" data-points="300" data-colors="#22AA99"></div>

                <div class="netdata-container-easypiechart" style="margin-right: 10px; width: 11%;" data-netdata="system.net" data-dimensions="received" data-chart-library="easypiechart" data-title="Net Inbound" data-width="11%" data-points="300" data-common-units="system.net.mainhead"></div>

                <div class="netdata-container-easypiechart" style="margin-right: 10px; width: 11%;" data-netdata="system.net" data-dimensions="sent" data-chart-library="easypiechart" data-title="Net Outbound" data-width="11%" data-points="300" data-common-units="system.net.mainhead"></div>

                <div class="netdata-container-easypiechart" style="margin-right: 10px; width: 9%;" data-netdata="system.ram" data-dimensions="used|buffers|active|wired" data-append-options="percentage" data-chart-library="easypiechart" data-title="Used RAM" data-units="%" data-easypiechart-max-value="100" data-width="9%" data-points="300" data-colors="#EE9911"></div>
            </div>
        </body>
        </html>
        """

        # 🚀 Render HTML di Streamlit
        st.components.v1.html(html_code, height=700, scrolling=False)