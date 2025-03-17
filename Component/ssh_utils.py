import paramiko
import streamlit as st

def connect_to_server(host, username, password):
    """Membuat koneksi SSH ke server."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=username, password=password)
        return ssh
    except Exception as e:
        st.error(f"❌ Gagal terhubung ke server {host}: {e}")
        return None

def remote_exec(ssh, command, password=None, use_sudo=False):
    """Menjalankan perintah di server remote melalui SSH."""
    if use_sudo:
        command = "sudo " + command
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        if password:
            stdin.write(password + "\n")
            stdin.flush()
    else:
        stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return output, err

def connect_to_server(host, username, password):
    """Membuat koneksi SSH ke server."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=username, password=password)
        return ssh
    except Exception as e:
        st.error(f"❌ Gagal terhubung ke server {host}: {e}")
        return None

def remote_exec(ssh, command, password=None, use_sudo=False):
    """Menjalankan perintah di server remote melalui SSH."""
    if use_sudo:
        command = "sudo " + command
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        if password:
            stdin.write(password + "\n")
            stdin.flush()
    else:
        stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return output, err

def interactive_ssh(ssh, command):
    """Menjalankan perintah di server dan mengembalikan output real-time."""
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    output = ""
    for line in iter(stdout.readline, ""):
        output += line
        st.text(line.strip())  # Tampilkan output langsung di Streamlit
    return output
