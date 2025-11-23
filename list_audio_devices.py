#!/usr/bin/env python3
"""
List all available audio devices to help identify Respeaker HAT.
"""

import sounddevice as sd

print("=" * 70)
print("Available Audio Devices")
print("=" * 70)
print()

devices = sd.query_devices()
default_input = sd.default.device[0]
default_output = sd.default.device[1]

print("INPUT DEVICES (Microphones):")
print("-" * 70)
for i, device in enumerate(devices):
    if device['max_input_channels'] > 0:
        default_marker = " <-- DEFAULT INPUT" if i == default_input else ""
        print(f"  [{i}] {device['name']}")
        print(f"      Channels: {device['max_input_channels']}, "
              f"Sample Rate: {device['default_samplerate']} Hz{default_marker}")
        print()

print()
print("OUTPUT DEVICES (Speakers):")
print("-" * 70)
for i, device in enumerate(devices):
    if device['max_output_channels'] > 0:
        default_marker = " <-- DEFAULT OUTPUT" if i == default_output else ""
        print(f"  [{i}] {device['name']}")
        print(f"      Channels: {device['max_output_channels']}, "
              f"Sample Rate: {device['default_samplerate']} Hz{default_marker}")
        print()

print()
print("=" * 70)
print("Respeaker 2-Mic Pi HAT typically appears as:")
print("  - 'seeed-2mic-voicecard' or similar")
print("  - May show as both input and output device")
print("=" * 70)
print()
print("To use these devices, update config.yaml:")
print("  audio:")
print("    input_device_index: <INPUT_DEVICE_NUMBER>")
print("    output_device_index: <OUTPUT_DEVICE_NUMBER>")
print()

