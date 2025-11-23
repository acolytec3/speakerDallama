# Audio Device Configuration Guide

## Finding Your Respeaker 2-Mic Pi HAT Devices

### Method 1: Using the Helper Script (Recommended)

Run the helper script to list all audio devices:

```bash
python3 list_audio_devices.py
```

This will show:
- All input devices (microphones) with their device numbers
- All output devices (speakers) with their device numbers
- Which device is currently set as default

Look for devices named:
- `seeed-2mic-voicecard` (most common)
- `seeed-voicecard`
- Or similar Seeed-related names

### Method 2: Using ALSA Commands

```bash
# List all audio cards
arecord -l

# List playback devices
aplay -l

# Test recording (should use Respeaker if it's default)
arecord -d 5 test.wav

# Test playback
aplay test.wav
```

### Method 3: Using Python Directly

```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

## Updating config.yaml

Once you've identified your device numbers:

1. **Open config.yaml**
2. **Find the audio section**:
   ```yaml
   audio:
     input_device_index: null
     output_device_index: null
   ```

3. **Replace `null` with the device numbers**:
   ```yaml
   audio:
     input_device_index: 2  # Your Respeaker input device number
     output_device_index: 2  # Your Respeaker output device number (often same)
   ```

## Common Respeaker 2-Mic Pi HAT Setup

The Respeaker HAT typically:
- Appears as **one device** that handles both input and output
- Has device name containing "seeed" or "2mic"
- May be device index 2, 3, or higher (depending on other audio devices)

### Example Configuration

If your Respeaker is device 2:

```yaml
audio:
  input_device_index: 2
  output_device_index: 2
```

### If Using Separate Devices

If your microphone and speaker are different devices:

```yaml
audio:
  input_device_index: 2   # Respeaker microphone
  output_device_index: 1   # Different speaker device
```

## Testing Your Configuration

1. **List devices** to verify:
   ```bash
   python3 list_audio_devices.py
   ```

2. **Test with main.py**:
   ```bash
   python3 main.py --list-devices
   ```

3. **Run a test recording**:
   ```bash
   python3 main.py --once
   ```

## Troubleshooting

### "Device not found" error
- Verify device number with `list_audio_devices.py`
- Make sure device is not in use by another application
- Try setting to `null` to use default device

### No audio input/output
- Check Respeaker HAT is properly connected
- Verify ALSA sees the device: `arecord -l` and `aplay -l`
- Check permissions: `sudo usermod -a -G audio $USER` (then logout/login)

### Wrong device selected
- Run `list_audio_devices.py` again
- Check if device numbers changed after reboot
- Consider using device names instead (requires code modification)

## Using Default Device

If you want to use the system default (recommended for first-time setup):

```yaml
audio:
  input_device_index: null   # Uses system default input
  output_device_index: null   # Uses system default output
```

Make sure your Respeaker is set as the default device in ALSA:
```bash
# Set default card (adjust card number as needed)
sudo nano /etc/asound.conf
# Add: defaults.pcm.card 2
#      defaults.ctl.card 2
```

