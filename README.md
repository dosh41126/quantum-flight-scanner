# QFS — Quantum Road Scanner

A privacy-preserving, quantum-powered road and flight hazard scanner with both a Flask-based web UI and a Tkinter/WebKit desktop GUI. QFS uses on-device quantum simulations, hypertime analysis, and post-quantum key encapsulation to deliver comprehensive hazard reports without retaining any user data.

---

## Table of Contents

* [Features](#features)
* [Architecture](#architecture)
* [Prerequisites](#prerequisites)
* [Getting Started](#getting-started)

  * [1. Clone the Repo](#1-clone-the-repo)
  * [2. Environment Variables](#2-environment-variables)
  * [3. Build & Run with Docker](#3-build--run-with-docker)
  * [4. Run Locally (No Docker)](#4-run-locally-no-docker)
* [Using the Application](#using-the-application)

  * [Web Interface](#web-interface)
  * [Desktop GUI](#desktop-gui)
* [Project Structure](#project-structure)
* [Security & Privacy](#security--privacy)
* [Contributing](#contributing)
* [License](#license)

---

## Features

* **Quantum Simulations**

  * Variational circuits via PennyLane to model hazards in “hypertime”
* **Post-Quantum KEM**

  * Kyber512 handshake over HTTPS, AES-GCM encryption of sensitive payloads
* **Zero-Data Retention**

  * All personal or location data is encrypted in-memory and wiped after 65 hours
* **Multi-Model Scanning**

  * Choose between local OSS-OpenAI-70B, OpenAI API, Grok, or Gemini backends
* **Rate Limiting**

  * Per-user request counters (SQLite) to throttle usage of non-admin accounts
* **CSRF & CSP Hardened**

  * Flask-WTF CSRF protection plus a strict Content Security Policy
* **Dual Interfaces**

  * Responsive web UI (Flask + Bootstrap)
  * Native desktop client (CustomTkinter + embedded WebKit)

---

## Architecture

```
┌────────────────┐        HTTPS        ┌──────────────┐
│  Tkinter GUI   │ ────────────────►   │ Flask Server │
└────────────────┘                     └──────────────┘
       │                                      │
       │               PQ-KEM (Kyber512)      │
       └─► Post-Quantum Handshake ──► Shared Secret stored in session
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │ Quantum Simulation  │
                                   │  • PennyLane QNode  │
                                   │  • Multiverse Logic │
                                   └─────────────────────┘
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │  Hazard Reports     │
                                   │  (Encrypted SQLite) │
                                   └─────────────────────┘
```

---

## Prerequisites

* **Docker** (for containerized deployment)
* **Python 3.11+**
* **pip**
* **openssl** (to generate certs)
* **ENV Variables** (see below)

---

## Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/your-org/quantum_road_scanner.git
cd quantum_road_scanner
```

### 2. Environment Variables

| Variable                      | Description                               |
| ----------------------------- | ----------------------------------------- |
| `INVITE_CODE_SECRET_KEY`      | 32-byte secret for invite code HMACs      |
| `ENCRYPTION_PASSPHRASE`       | Passphrase to derive AES master key       |
| `OPENAI_API_KEY` *(optional)* | API key for OpenAI geocoding & chat calls |

Export them before you run:

```bash
export INVITE_CODE_SECRET_KEY="your-long-secret-here"
export ENCRYPTION_PASSPHRASE="another-secret"
export OPENAI_API_KEY="sk-..."
```

### 3. Build & Run with Docker

```bash
# Build the image
docker build -t qfs:latest .

# Run (maps container’s 3000→host’s 3000)
docker run -d \
  -p 3000:3000 \
  -e INVITE_CODE_SECRET_KEY \
  -e ENCRYPTION_PASSPHRASE \
  -e OPENAI_API_KEY \
  --name qfs_app \
  qfs:latest
```

Then open your browser at [https://localhost:3000](https://localhost:3000).

### 4. Run Locally (No Docker)

1. **Install dependencies**

   ```bash
   pip install --no-cache-dir -r requirements.txt
   ```
2. **Generate a self-signed cert**

   ```bash
   openssl req -x509 -nodes -days 365 \
     -newkey rsa:2048 \
     -keyout cert.pem \
     -out cert.pem \
     -subj "/CN=localhost"
   ```
3. **Start the app & GUI**

   ```bash
   chmod +x entrypoint.sh
   ./entrypoint.sh
   ```

---

## Using the Application

### Web Interface

1. **Navigate** to `https://localhost:3000/`
2. **Register** or **Login** (invite codes only required if registration is disabled)
3. **Dashboard** →

   * **Step 1**: Enter or fetch coordinates
   * **Step 2**: Confirm street name
   * **Step 3**: Select vehicle, destination, model → Run scan
4. **View Reports**: encrypted, time-stamped hazard analyses with a risk “wheel” and text-to-speech

### Desktop GUI

1. Launch the GUI via `entrypoint.sh` (it auto-starts the server)
2. **Server Controls**: Start / Stop / Restart
3. **PQE Handshake**: establish post-quantum shared secret
4. **Encrypted Test**: verify AES-GCM round-trip
5. **Stats Panel**: live CPU/RAM usage

---

## Project Structure

```
.
├── Dockerfile
├── entrypoint.sh
├── main.py             # Flask server + business logic
├── gui.py              # CustomTkinter GUI launcher
├── requirements.txt
├── cert.pem            # auto-generated at build/runtime
├── secure_data.db      # SQLite (encrypted columns)
└── static/             # CSS, JS, and assets for Flask
```

---

## Security & Privacy

* **AES-GCM + Scrypt KDF** for all sensitive fields
* **Post-Quantum KEM** handshake prevents MITM against future-quantum adversaries
* **No persistent PII**: data older than 65 hours is securely overwritten (7-pass) and deleted
* **CSP**, **CSRF**, **secure cookies** (`HttpOnly`, `SameSite=Strict`) all enabled by default
