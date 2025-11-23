# Speaker Dallama - STT/TTS Demo

A lightweight speech-to-text and text-to-speech demo for Raspberry Pi 3 with Respeaker 2-Mic Pi HAT.

## Features

- Real-time speech-to-text using Vosk
- Text-to-speech using Piper
- Console output of transcriptions

## Requirements

- Raspberry Pi 3 with Respeaker 2-Mic Pi HAT
- Python 3.7+
- Vosk model (download from https://alphacephei.com/vosk/models)
- Piper TTS binary

## Remote Development Setup

To develop on your Pi from your main computer, see **[SETUP_REMOTE.md](SETUP_REMOTE.md)** for detailed instructions on:
- Setting up SSH access
- Configuring Samba file sharing
- Using VS Code/Cursor Remote SSH
- Transferring files to the Pi

**Quick SSH setup:**
```bash
# On Pi: Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# On your dev machine: Connect
ssh pi@<PI_IP_ADDRESS>

# Transfer files
scp -r speakerDallama pi@<PI_IP_ADDRESS>:~/
```

## Installation

**Quick setup on Pi:**
```bash
# Run the setup script
chmod +x setup_pi.sh
./setup_pi.sh
```

**Manual installation:**

1. Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev libsndfile1
```

2. Install Python dependencies (using `uv` - recommended, or `pip3`):
```bash
# Using uv (faster, recommended):
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Or using pip3:
pip3 install --user -r requirements.txt
```

3. Download a Vosk model (e.g., vosk-model-small-en-us-0.15) and extract it

4. Install Piper TTS (see Piper documentation)

## Configuration

Edit `config.yaml` to set:
- Vosk model path
- Piper model path and voice
- Audio device IDs (optional)

## Usage

```bash
python3 main.py
```

Speak into the microphone. The transcribed text will appear in the console, and then be read back via TTS.

