#!/bin/bash
# Setup script for Raspberry Pi 3
# Run this on your Pi to prepare the development environment

set -e

echo "=========================================="
echo "Raspberry Pi 3 Development Setup"
echo "=========================================="
echo ""

# Update system
echo "[1/6] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install development tools
echo "[2/6] Installing development tools..."
sudo apt-get install -y \
  git \
  portaudio19-dev \
  libsndfile1 \
  vim \
  nano \
  build-essential \
  curl

# Install uv (fast Python package installer)
echo "  Installing uv..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "  uv installed successfully"
else
    echo "  uv is already installed: $(uv --version)"
fi

# Enable SSH
echo "[3/6] Enabling SSH..."
sudo systemctl enable ssh
sudo systemctl start ssh

# Show IP address
echo ""
echo "=========================================="
echo "Your Pi's IP addresses:"
hostname -I
echo "=========================================="
echo ""

# Install Python dependencies with uv
echo "[4/6] Installing Python dependencies with uv..."
# Ensure uv is in PATH
export PATH="$HOME/.cargo/bin:$PATH"

if [ -f "requirements.txt" ]; then
    # uv can create venv and install in one command
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
    echo "  Dependencies installed in virtual environment"
else
    echo "  Warning: requirements.txt not found. Install manually:"
    echo "  uv pip install vosk pyaudio pyyaml numpy"
fi

# Note about virtual environment
echo "[5/6] Virtual environment setup..."
if [ -d ".venv" ]; then
    echo "  Virtual environment created at .venv"
    echo "  Activate with: source .venv/bin/activate"
fi

# Set up git (if not already)
echo "[6/6] Checking git configuration..."
if [ -z "$(git config --global user.name)" ]; then
    echo "  Git not configured. Run these commands:"
    echo "  git config --global user.name 'Your Name'"
    echo "  git config --global user.email 'your.email@example.com'"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Add uv to PATH permanently (if not already):"
echo "   echo 'export PATH=\"\$HOME/.cargo/bin:\$PATH\"' >> ~/.bashrc"
echo "   source ~/.bashrc"
echo "2. Activate virtual environment: source .venv/bin/activate"
echo "3. Download Vosk model from: https://alphacephei.com/vosk/models"
echo "4. Install Piper TTS (see README.md)"
echo "5. Update config.yaml with correct paths"
echo "6. Run: python3 main.py"
echo ""
echo "Note: uv is installed at ~/.cargo/bin/uv"
echo "      Make sure it's in your PATH for future sessions"
echo ""

