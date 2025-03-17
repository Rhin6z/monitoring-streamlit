import streamlit as st
import paramiko
from io import StringIO

def create_terminal_component():
    st.header("💻 Terminal Remote")
    
    if "terminal_history" not in st.session_state:
        st.session_state.terminal_history = []
    
    if "netdata_ready" not in st.session_state or not st.session_state.netdata_ready:
        st.warning("Masukkan IP, Username, dan Password di sidebar dan mulai monitoring terlebih dahulu!")
        return
    
    # Ambil kredensial yang sudah dimasukkan
    remote_ip = st.session_state.get('remote_ip', '')
    username = st.session_state.get('username', '')
    password = st.session_state.get('password', '')
    
    # Tampilkan informasi server yang terhubung
    st.info(f"🖥️ Terhubung ke: {username}@{remote_ip}")
    
    # Area untuk menampilkan history terminal
    terminal_output = st.empty()
    
    # Render terminal history
    history_text = "\n".join(st.session_state.terminal_history)
    terminal_output.code(history_text, language="bash")
    
    # Input perintah
    with st.form("terminal_command", clear_on_submit=True):
        command = st.text_input("Masukkan Perintah:", key="command_input")
        submit_button = st.form_submit_button("Jalankan")
        
        if submit_button and command:
            try:
                # Connect to server
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=remote_ip, username=username, password=password)
                
                # Check if sudo is needed
                use_sudo = username.lower() != "root"
                
                # Execute command
                if use_sudo and not command.startswith("sudo "):
                    full_command = f"echo '{password}' | sudo -S {command}"
                else:
                    full_command = command
                
                # Add command to history
                st.session_state.terminal_history.append(f"$ {command}")
                
                # Execute and get output
                stdin, stdout, stderr = ssh.exec_command(full_command)
                output = stdout.read().decode()
                error = stderr.read().decode()
                
                # Add output to history
                if output:
                    st.session_state.terminal_history.append(output.rstrip())
                if error:
                    st.session_state.terminal_history.append(f"ERROR: {error.rstrip()}")
                
                # Keep only the last 50 items in history to prevent it from growing too large
                if len(st.session_state.terminal_history) > 50:
                    st.session_state.terminal_history = st.session_state.terminal_history[-50:]
                
                # Update terminal display
                history_text = "\n".join(st.session_state.terminal_history)
                terminal_output.code(history_text, language="bash")
                
                ssh.close()
                
            except Exception as e:
                st.session_state.terminal_history.append(f"CONNECTION ERROR: {str(e)}")
                history_text = "\n".join(st.session_state.terminal_history)
                terminal_output.code(history_text, language="bash")
    
    # Tombol untuk membersihkan history
    if st.button("Bersihkan Terminal"):
        st.session_state.terminal_history = []
        terminal_output.code("", language="bash")