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

“Imagine, if you will, a traveler gliding across the silver veins of every highway on this pale blue dot we call home. In the passenger seat sits not merely a map or a radio, but a companion born of the quantum realm—an ever-vigilant sentinel against unseen hazards. This is the promise of QFS, the Quantum Road Scanner.”

From a cosmic vantage, our roads are like celestial currents, flowing with vehicles instead of solar winds. QFS harnesses the curious dance of qubits and hypertime, projecting myriad possible futures in the flicker of an eye. Armed with a laptop’s GPU nestled in your dashboard, QFS unfolds a tapestry of simulations—each scenario a brushstroke in a grand probabilistic fresco. It is as if a flock of quantum nanobots, each exploring alternate timelines, whispers their findings to you in real time, saying: “Here lies debris. There, a danger. Steer gently, and you may grace the horizon unscathed.”

Under the hood, the program orchestrates an elegant ballet: geolocation pinpoints your cosmic coordinates, a reverse-geocoder translates them into human-familiar street names, and a hybrid of local and API-driven models (from OSS-70B to OpenAI’s titans) weaves raw data into sensibly choreographed risk assessments. All the while, post-quantum key exchanges safeguard your journey’s intimate details, ensuring that the story of your travels remains yours alone. It is a marriage of the most advanced cryptography with the most imaginative quantum algorithms—proof that even on asphalted pathways, our innate yearning for privacy and exploration need not conflict.

What might it be like to sit behind the wheel, feeling the hum of a mid-sized GPU beneath your console, as QFS continually scans the road ahead? Imagine the quiet confidence of knowing that, powered by hypertime analysis, you carry not just one forecast, but a symphony of potential outcomes—each weighted, each considered. In heavy rain or under the dazzling glare of city lights, those virtual nanobots parse CPU and RAM usage, weigh quantum noise, and deliver you a distilled recommendation: low risk, medium caution, or an urgent detour. The interface—a sleek web view embedded in a desktop‐style GUI—feels like conversing with a trusted co-pilot.

Yet QFS is more than software; it is a testament to our species’ capacity to blend wonder with rigor. It draws from the quantum depths, yet remains grounded in the everyday: the driver’s seat of a car, the hum of a laptop, the gentle click of a “Start Scan” button. It honors both the grand theories of multidimensional time and the humble necessity of safe passage from point A to point B.

In the end, QFS invites us to embrace the profound unity of the cosmos and the quotidian. It reminds us that, whether charting the stars or navigating suburban boulevards, knowledge is our compass. And with quantum‐powered insight on every dash, we may traverse our terrestrial highways not as passive travelers, but as active explorers of a universe constantly in flux.

