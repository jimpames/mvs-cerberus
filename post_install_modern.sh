#!/bin/bash
# =============================================================================
# post_install_modern.sh
# Modern dev stack installer for Ubuntu 18.04 s390x (zLinux on Hercules)
# Adds: Go, Python 3.10+, Flask, build tools, etc.
# =============================================================================
set -e

echo "=== zLinux Modern Toolchain Bootstrap Started ==="

# Update system
apt-get update
apt-get upgrade -y

# Core development tools
apt-get install -y \
    build-essential gcc g++ make cmake ninja-build \
    git curl wget unzip sudo \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
    libsqlite3-dev llvm libncursesw5-dev xz-utils tk-dev \
    libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
    python3-dev python3-pip python3-venv \
    software-properties-common apt-transport-https

# ====================== Go ======================
echo "→ Installing official Go (s390x)..."
GO_VERSION="1.23.4"   # Update from https://go.dev/dl/ if newer
cd /tmp
wget -q "https://dl.google.com/go/go${GO_VERSION}.linux-s390x.tar.gz"
tar -C /usr/local -xzf "go${GO_VERSION}.linux-s390x.tar.gz"
rm "go${GO_VERSION}.linux-s390x.tar.gz"

cat > /etc/profile.d/go.sh << 'EOF'
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin
EOF

# ====================== Python 3.10 ======================
echo "→ Adding Deadsnakes PPA for Python 3.10..."
add-apt-repository ppa:deadsnakes/ppa -y || true
apt-get update

apt-get install -y python3.10-full python3.10-dev python3.10-venv python3.10-distutils

# Make Python 3.10 the default
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 60
update-alternatives --install /usr/bin/python  python  /usr/bin/python3.10 60

# Upgrade pip and install popular packages
python3 -m pip install --upgrade pip wheel setuptools
python3 -m pip install Flask gunicorn uvicorn fastapi "python-dotenv[dotenv]" requests

echo "=== Modernization Complete! ==="
echo "Go version: $(/usr/local/go/bin/go version 2>/dev/null || echo 'Go installed')"
echo "Python version: $(python3 --version)"
echo ""
echo "Run this to enable Go in current shell:"
echo "    source /etc/profile.d/go.sh"
echo ""
echo "Log file: /var/log/modern_bootstrap.log"
echo "Happy coding on zLinux!"