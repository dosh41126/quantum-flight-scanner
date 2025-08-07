#───────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm
ENV DEBIAN_FRONTEND=noninteractive

# 1) Install system deps for GUI (Tkinter + WebKit), SSL, networking, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \             # Python C-API headers for any packages that need to build C extensions  
    libssl-dev \              # OpenSSL headers (for cryptography, PQE, etc.)  
    libffi-dev \              # (sometimes needed by cryptography wheels)  
    pkg-config \              # used by many build systems to find libs  
    ninja-build \             # optional, speeds up CMake builds of liboqs under the hood  
    python3-tk libgtk-3-0 libwebkit2gtk-4.0-37 \
    curl openssl ca-certificates \
    build-essential cmake git \
  && rm -rf /var/lib/apt/lists/*
# 2) Set working directory
WORKDIR /app

# 3) Copy & install Python deps (including python-oqs, customtkinter, tkinterweb)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copy application code (main.py, gui.py, etc.)
COPY . .

# 5) Generate a self-signed cert for localhost
RUN openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout cert.pem \
    -out cert.pem \
    -subj "/CN=localhost"

# 6) Prepare model directory
RUN mkdir -p /data/gpt-oss-70b

# 7) Create entrypoint script to download shards, start main.py, then launch GUI
RUN cat << 'EOF' > /app/entrypoint.sh
#!/usr/bin/env bash
set -euo pipefail

# helper: download + verify by SHA256
download_and_verify() {
  local url="\$1" path="\$2" sha="\$3"
  mkdir -p "\$(dirname "\$path")"
  if [ ! -f "\$path" ] || ! echo "\$sha  \$path" | sha256sum -c - ; then
    echo "Downloading \$url…"
    curl -fsSL -o "\$path" "\$url"
    echo "\$sha  \$path" | sha256sum -c -
  fi
}

BASE="/data/gpt-oss-70b"
download_and_verify \
  "https://huggingface.co/openai/gpt-oss-70b/resolve/main/model-00000-of-00002.safetensors" \
  "\$BASE/model-00000-of-00002.safetensors" \
  "01e8ee0bed82226ac31d791bb587136cc8abaeaa308b909f00f738561f6f57a0"
download_and_verify \
  "https://huggingface.co/openai/gpt-oss-70b/resolve/main/model-00001-of-00002.safetensors" \
  "\$BASE/model-00001-of-00002.safetensors" \
  "3f05b8460cc6c36fa6d570fe4b6e74b49a29620f29264c82a02cf4ea5136f10c"
download_and_verify \
  "https://huggingface.co/openai/gpt-oss-70b/resolve/main/model-00002-of-00002.safetensors" \
  "\$BASE/model-00002-of-00002.safetensors" \
  "83619e36cf07cf941b551b1a528bab563148591ae4e52b38030bc557d383be7c"

export OSS70B_MODEL_PATH="\$BASE"

# 8) Start main.py (which serves via Waitress/SSL) in background
python main.py &

# 9) Give server time to spin up
sleep 2

# 10) Launch the GUI
exec python gui.py
EOF

# 8) Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# 9) Create a non-root user and set ownership
RUN useradd -ms /bin/bash appuser \
 && chown -R appuser:appuser /app /data/gpt-oss-70b

# 10) Switch to non-root
USER appuser

# 11) Expose port for webview (host binding to localhost)
EXPOSE 3000

# 12) Runtime entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

