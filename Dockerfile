# Use a lightweight Python image as the base
FROM python:3.11-slim

# Install bash (for our entrypoint) and any build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash build-essential cmake git \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install all Python dependencies except llama-cpp-python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create the entrypoint script in-line
RUN cat << 'EOF' > /entrypoint.sh
#!/usr/bin/env bash
set -e

echo "Checking for NVIDIA GPU support..."
if command -v nvidia-smi >/dev/null 2>&1 ; then
  echo "→ NVIDIA GPU detected. Installing llama-cpp-python with CUDA/cuBLAS support..."
  CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 \
    pip install --no-cache-dir --upgrade --force-reinstall \
      --no-binary llama-cpp-python llama-cpp-python

elif [ -x "$(command -v rocminfo)" ] ; then
  echo "→ AMD GPU (ROCm) detected. Installing llama-cpp-python with hipBLAS support..."
  CMAKE_ARGS="-DGGML_HIPBLAS=on" FORCE_CMAKE=1 \
    pip install --no-cache-dir --upgrade --force-reinstall \
      --no-binary llama-cpp-python llama-cpp-python

else
  echo "→ No GPU found. Installing llama-cpp-python (CPU-only wheel)..."
  pip install --no-cache-dir --upgrade llama-cpp-python
fi

echo "Starting application…"
exec "$@"
EOF

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

# Prepare secure directories and files
RUN useradd -ms /bin/bash appuser \
 && mkdir -p /home/appuser/.keys /home/appuser/data \
 && chmod 700 /home/appuser/.keys /home/appuser/data \
 && touch /home/appuser/data/secure_data.db \
 && chmod 600 /home/appuser/data/secure_data.db \
 && chown -R appuser:appuser /home/appuser

# Secure /app directory
RUN chmod -R 755 /app && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port that waitress will listen on
EXPOSE 3000

# Use our entrypoint to detect GPU & install llama-cpp-python, then launch the app
ENTRYPOINT ["/entrypoint.sh"]
CMD ["waitress-serve", "--host=0.0.0.0", "--port=3000", "--threads=4", "main:app"]
