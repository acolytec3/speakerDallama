# Troubleshooting Guide

## PyAudio Build Errors

If you encounter PyAudio build errors (especially with Python 3.13+), this project now uses `sounddevice` instead of PyAudio, which:
- Works with Python 3.13+
- Doesn't require compilation
- Has better cross-platform support

## Installation Issues

### "pip3 not found" or "uv not found"
- See [INSTALL_PIP3.md](INSTALL_PIP3.md) or [INSTALL_UV.md](INSTALL_UV.md)
- Make sure PATH includes `~/.cargo/bin` for uv

### "portaudio19-dev not found"
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev libsndfile1
```

### "sounddevice installation fails"
- Make sure portaudio19-dev is installed
- Try: `uv pip install sounddevice soundfile`

## Audio Device Issues

### "No audio input devices found"
```bash
# List audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Check if Respeaker is detected
arecord -l
```

### "Permission denied" for audio
```bash
# Add user to audio group
sudo usermod -a -G audio $USER
# Log out and back in, or reboot
```

### Wrong audio device selected
- Run: `python3 main.py --list-devices`
- Update `config.yaml` with correct device indices

## Vosk Model Issues

### "Vosk model not found"
- Download a model from: https://alphacephei.com/vosk/models
- Extract to a directory
- Update `config.yaml` with the correct path
- Recommended for Pi 3: `vosk-model-small-en-us-0.15`

### "Out of memory" errors
- Use a smaller Vosk model
- Close other applications
- Consider using `vosk-model-small-en-us-0.15` instead of larger models

## Piper TTS Issues

### "Piper binary not found"
- Install Piper TTS separately
- Download from: https://github.com/rhasspy/piper/releases
- Extract and update `config.yaml` with binary path

### "Piper model not found"
- Download a voice model from Piper repository
- Update `config.yaml` with correct model and config paths

### Alternative: Use eSpeak (lighter but lower quality)
```bash
sudo apt-get install espeak espeak-data
# Then modify tts_piper.py to use espeak instead
```

## Runtime Issues

### "No speech detected"
- Check microphone is working: `arecord -d 5 test.wav && aplay test.wav`
- Adjust `silence_threshold` in `config.yaml` (lower = more sensitive)
- Check audio device selection

### Transcription is slow
- Use smaller Vosk model
- Reduce `chunk_size` in config
- Close other applications

### Audio playback issues
- Check speaker is connected
- Test with: `aplay /usr/share/sounds/alsa/Front_Left.wav`
- Verify output device in config

## Python Version Issues

### Python 3.13 compatibility
- This project uses `sounddevice` which supports Python 3.13+
- If using older Python, you may need to use PyAudio instead

### "Module not found" errors
- Make sure virtual environment is activated: `source .venv/bin/activate`
- Reinstall dependencies: `uv pip install -r requirements.txt`

## Network/SSH Issues

### Can't connect via SSH
- Check Pi is on same network
- Verify SSH is enabled: `sudo systemctl status ssh`
- Check firewall: `sudo ufw status`

### File transfer issues
- Use `scp` or `rsync` for file transfer
- Or use VS Code Remote SSH extension



