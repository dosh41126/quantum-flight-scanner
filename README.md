
# Quantum Flight Scanner (QFS)
All-in-one Flask app that generates **runway-debris / airborne-hazard** briefings from a latitude & longitude.  
Everything lives in **`main.py`** – no blueprints, no extra modules.

---

## Features
| Area | What it does |
|------|--------------|
| Reverse-Geocoding | Uses OpenAI if an API-key is supplied, otherwise a local city heuristic. |
| Hazard Analysis   | GPT-4o prompt plus a small PennyLane quantum circuit for risk scoring. |
| Persistence       | SQLite (`secure_data.db`) with column-level AES-GCM encryption. |
| Auth & Rate-Limit | Optional invite-code flow, Argon2id passwords, per-user throttling. |
| UI                | Bootstrap 5 + Speech-Synthesis with colour-coded risk wheels. |
| Docker-ready      | Single Dockerfile (rootless) – see below. |

---

## Required Environment Variables
Variable | Purpose
---------|---------
`INVITE_CODE_SECRET_KEY` | HMAC seed that also becomes Flask’s `SECRET_KEY` – **32 random bytes**, base64 is fine.
`ENCRYPTION_PASSPHRASE` | Master passphrase stretched with Argon2id → 256-bit key to encrypt the DB. **Changing later breaks old data.**
`OPENAI_API_KEY` | _(optional but recommended)_ Enables GPT-4o reverse-geocoding & hazard reports. App still runs without it.

---

## Local quick-start (no Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export INVITE_CODE_SECRET_KEY=$(openssl rand -base64 32)
export ENCRYPTION_PASSPHRASE='super-long-passphrase'
export OPENAI_API_KEY='sk-xxxxxxxx'        # optional

python main.py
# ⇒ http://localhost:3000
```

## Container usage

### 1 / Build the image

```bash
docker build -t qfs .
```

### 2 / Run the container

```bash
docker run --rm -p 3000:3000 \
  -e INVITE_CODE_SECRET_KEY="$(openssl rand -base64 32)" \
  -e ENCRYPTION_PASSPHRASE="super-long-passphrase" \
  -e OPENAI_API_KEY="sk-xxxxxxxx" \
  --name qfs \
  qfs
```

*The Dockerfile already creates a non-root `appuser`, locks down `/home/appuser/.keys` & the SQLite file, and launches QFS under `waitress`.*


## Development tips

* Database lives in `/home/appuser/data/secure_data.db` inside the container.
  Mount a volume there if you want persistence:
  `-v ./db:/home/appuser/data`
* Invite-codes are optional **only** when registration is disabled in the admin panel.
* `main.py` contains **everything** (helpers, routes, forms, quantum code) – search for `# scanner.py` or `@app.route` to navigate.

---

## License

GPL3Multiverse ✈️.
