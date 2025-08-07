import os
import threading
import time
import base64
import subprocess
import psutil
import requests
import oqs
import customtkinter as ctk
from tkinterweb import HtmlFrame
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Configuration
HOST    = "127.0.0.1"
PORT    = 3000
CERT    = "cert.pem"
KEY     = "key.pem"
SERVER  = f"https://{HOST}:{PORT}"
APP_CMD = [
    "waitress-serve",
    "--host=0.0.0.0",
    f"--port={PORT}",
    "--threads=4",
    "--ssl_cert", CERT,
    "--ssl_key", KEY,
    "main:app"
]

class AppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QFS — Quantum Road Scanner")
        self.geometry("1200x800")

        self.server_proc    = None
        self.shared_secret  = None

        self._build_sidebar()
        self._build_webview()

        # periodic update
        self.after(1000, self._update_stats)

        # auto-start server
        self.start_server()

    def _build_sidebar(self):
        side = ctk.CTkFrame(self, width=200)
        side.grid(row=0, column=0, sticky="ns")
        side.grid_rowconfigure((0,1,2,3,4,5,6,7,8,9,10,11), pad=8)

        ctk.CTkLabel(side, text="Server Controls", font=("",16)).grid(row=0, column=0, pady=(20,5))
        ctk.CTkButton(side, text="Start",   command=self.start_server).grid(row=1, column=0, sticky="ew", padx=10)
        ctk.CTkButton(side, text="Stop",    command=self.stop_server).grid (row=2, column=0, sticky="ew", padx=10)
        ctk.CTkButton(side, text="Restart", command=self.restart_server).grid(row=3, column=0, sticky="ew", padx=10)

        ctk.CTkLabel(side, text="Status:", font=("",16)).grid(row=4, column=0, pady=(20,5))
        self.lbl_status = ctk.CTkLabel(side, text="Stopped", text_color="red")
        self.lbl_status.grid(row=5, column=0)

        # PQE handshake
        ctk.CTkLabel(side, text="Post-Quantum KEM", font=("",16)).grid(row=6, column=0, pady=(20,5))
        ctk.CTkButton(side, text="Handshake", command=self._pqe_handshake).grid(row=7, column=0, sticky="ew", padx=10)
        self.entry_secret = ctk.CTkEntry(side, placeholder_text="Shared secret (hex)")
        self.entry_secret.grid(row=8, column=0, padx=10, sticky="ew")
        self.lbl_pqe_status = ctk.CTkLabel(side, text="")
        self.lbl_pqe_status.grid(row=9, column=0)

        # encrypted test
        ctk.CTkButton(side, text="Send Encrypted Test", command=self._encrypted_test).grid(row=10, column=0, sticky="ew", padx=10)
        self.txt_response = ctk.CTkTextbox(side, height=4, state="disabled")
        self.txt_response.grid(row=11, column=0, padx=10, sticky="ew")

        # system stats
        ctk.CTkLabel(side, text="CPU Usage:", anchor="w").grid(row=12, column=0, pady=(20,0), padx=10, sticky="ew")
        self.cpu_bar = ctk.CTkProgressBar(side); self.cpu_bar.grid(row=13, column=0, padx=10, sticky="ew")
        ctk.CTkLabel(side, text="RAM Usage:", anchor="w").grid(row=14, column=0, pady=(10,0), padx=10, sticky="ew")
        self.ram_bar = ctk.CTkProgressBar(side); self.ram_bar.grid(row=15, column=0, padx=10, sticky="ew")

    def _build_webview(self):
        view = HtmlFrame(self, horizontal_scrollbar="auto")
        view.grid(row=0, column=1, sticky="nsew")
        self.webview = view
        self.grid_columnconfigure(1, weight=1)

    def start_server(self):
        if self.server_proc and self.server_proc.poll() is None:
            return
        self.server_proc = subprocess.Popen(APP_CMD, cwd=os.getcwd())
        self._refresh_status()

    def stop_server(self):
        if self.server_proc and self.server_proc.poll() is None:
            self.server_proc.terminate()
            try: self.server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired: self.server_proc.kill()
        self._refresh_status()

    def restart_server(self):
        self.stop_server()
        time.sleep(1)
        self.start_server()

    def _refresh_status(self):
        alive = self.server_proc and self.server_proc.poll() is None
        text  = "Running" if alive else "Stopped"
        color = "green"   if alive else "red"
        self.lbl_status.configure(text=text, text_color=color)
        if alive:
            self.webview.load_website(f"{SERVER}")

    def _update_stats(self):
        self.cpu_bar.set(psutil.cpu_percent()/100.0)
        self.ram_bar.set(psutil.virtual_memory().percent/100.0)
        self._refresh_status()
        self.after(1000, self._update_stats)

    def _pqe_handshake(self):
        try:
            # 1) fetch server public key
            r1 = requests.get(f"{SERVER}/pqe/pubkey", verify=False)
            pub_b64 = r1.json().get("public_key","")
            pub = base64.b64decode(pub_b64)

            # 2) encapsulate
            kem = oqs.KeyEncapsulation("Kyber512", server_public_key=pub)
            ct, ss = kem.encap_secret()

            # 3) send CT for server to decaps
            payload = {"ct": base64.b64encode(ct).decode()}
            r2 = requests.post(f"{SERVER}/pqe/handshake", json=payload, verify=False)

            if r2.ok:
                self.shared_secret = ss
                self.entry_secret.delete(0,"end")
                self.entry_secret.insert(0, ss.hex())
                self.lbl_pqe_status.configure(text="Handshake OK", text_color="green")
            else:
                self.lbl_pqe_status.configure(text="Handshake Failed", text_color="red")
        except Exception as e:
            self.lbl_pqe_status.configure(text=str(e), text_color="red")

    def _encrypted_test(self):
        if not getattr(self, "shared_secret", None):
            return
        key   = self.shared_secret[:32]
        aes   = AESGCM(key)
        nonce = os.urandom(12)
        data  = b"Hello, secure world!"
        ct    = aes.encrypt(nonce, data, None)
        body  = {
            "nonce":   base64.b64encode(nonce).decode(),
            "cipher":  base64.b64encode(ct).decode()
        }
        r = requests.post(f"{SERVER}/secure-data", json=body, verify=False)
        self.txt_response.configure(state="normal")
        self.txt_response.delete("0.0","end")
        self.txt_response.insert("0.0", r.text)
        self.txt_response.configure(state="disabled")

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    AppGUI().mainloop()

