# Speaker Dallama - Voice Assistant

A voice-controlled assistant for Raspberry Pi with Respeaker 2-Mic Pi HAT. Features wake word detection, speech-to-text, LLM integration, text-to-speech, and LED visual feedback.

## Features

- **Wake Word Detection** - Uses OpenWakeWord (e.g., "Hey Jarvis")
- **Speech-to-Text** - Real-time transcription using Vosk
- **LLM Integration** - Connects to Dallama chat server for intelligent responses
- **Text-to-Speech** - Uses Piper or Flite TTS engines
- **LED Visual Feedback** - APA102 LEDs show status (wake word, listening, thinking, speaking)

## Hardware Requirements

- Raspberry Pi 3 (or newer)
- Respeaker 2-Mic Pi HAT
- MicroSD card with Raspberry Pi OS
- Power supply for Raspberry Pi

## Quick Start

### 1. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev libsndfile1 python3-pip python3-venv
```

### 2. Enable SPI (for LEDs)

```bash
sudo raspi-config
# Navigate to: Interface Options -> SPI -> Enable
# Reboot after enabling
sudo reboot
```

### 3. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
### 4. Download Vosk Model

Download a Vosk model and extract it in the project directory:
```bash
# Example: Download small English model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

### 5. Install TTS Engine

**Option A: Piper TTS (recommended)**
- Download from: https://github.com/rhasspy/piper/releases
- Extract and place `piper` binary in `/usr/local/bin/piper` or update path in `config.yaml`
- Download voice models from: https://github.com/rhasspy/piper/releases

**Option B: Flite TTS (lightweight)**
```bash
sudo apt-get install flite
```

### 6. Configure Audio Devices

Find your Respeaker HAT device:
```bash
python3 list_audio_devices.py
```

Update `config.yaml` with the device index if needed:
```yaml
audio:
  input_device_index: 2   # Your Respeaker input device
  output_device_index: 2   # Your Respeaker output device
```

### 7. Configure LLM (Optional)

If using LLM integration, update `config.yaml`:
```yaml
llm:
  enabled: true
  base_url: "http://YOUR_LLM_SERVER_IP:3000"
```

## Configuration

Edit `config.yaml` to customize:

- **Vosk model path** - Path to your downloaded Vosk model
- **TTS engine** - Choose 'piper' or 'flite'
- **Wake word** - Model name (default: 'hey_jarvis')
- **Audio devices** - Input/output device indices
- **LLM server** - URL of your Dallama chat server

## Usage

### Basic Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python3 main.py
```

The application will:
1. Wait for wake word ("Hey Jarvis")
2. Listen for your speech
3. Transcribe it
4. Send to LLM (if enabled)
5. Speak the response

### Command Line Options

```bash
# Use Flite TTS instead of Piper
python3 main.py --tts-engine flite

# Run once instead of continuous loop
python3 main.py --once

# List available audio devices
python3 main.py --list-devices

# Use custom config file
python3 main.py --config my_config.yaml
```

### Testing LEDs

Test LED patterns:
```bash
python3 pixels.py
```

## Project Structure

```
speakerDallama/
├── main.py              # Main application
├── config.yaml          # Configuration file
├── requirements.txt     # Python dependencies
├── stt_vosk.py         # Speech-to-text module
├── tts_piper.py        # Piper TTS module
├── tts_flite.py        # Flite TTS module
├── wake_word.py        # Wake word detection
├── llm_dallama.py      # LLM integration
├── pixels.py           # LED control
├── list_audio_devices.py # Audio device helper
└── vosk-model-*/       # Vosk model directory
```

## LED Patterns

The LEDs show different patterns for each state:

- **Wake Word Detected** - Fade in animation
- **Listening/Transcribing** - Solid on
- **Thinking (LLM)** - Rotating pattern
- **Speaking** - Pulsing pattern
- **Off** - LEDs off

## Troubleshooting

### LEDs Not Working

1. **Check SPI is enabled:**
   ```bash
   ls -l /dev/spi*
   # Should show /dev/spidev0.0 and /dev/spidev0.1
   ```

### Audio Not Working

1. **List audio devices:**
   ```bash
   python3 list_audio_devices.py
   ```

2. **Check Respeaker HAT is detected:**
   ```bash
   arecord -l
   aplay -l
   ```

3. **Update config.yaml with correct device indices**

### Wake Word Not Detecting

1. **Check microphone is working:**
   ```bash
   arecord -d 5 test.wav
   aplay test.wav
   ```

2. **Adjust silence threshold in config.yaml:**
   ```yaml
   recording:
     silence_threshold: 500  # Lower = more sensitive
   ```

### LLM Connection Issues

1. **Check LLM server is running:**
   ```bash
   curl http://YOUR_SERVER_IP:3000/health
   ```

2. **Verify base_url in config.yaml**

## Additional Documentation

- **[AUDIO_SETUP.md](AUDIO_SETUP.md)** - Detailed audio device configuration
- **[SETUP_REMOTE.md](SETUP_REMOTE.md)** - Remote development setup
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

## License

This project uses various open-source libraries. Please refer to their respective licenses.
