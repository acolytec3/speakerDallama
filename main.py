#!/usr/bin/env python3
"""
Main application for STT/TTS demo.

Records speech, transcribes with Vosk, and reads back with TTS.
"""

import yaml
import os
import sys
import signal
from stt_vosk import VoskSTT
from tts_piper import PiperTTS
from wake_word import WakeWordDetector


class VoiceDemo:
    def __init__(self, config_path='config.yaml'):
        """Initialize the voice demo application."""
        self.config = self.load_config(config_path)
        self.stt = None
        self.tts = None
        self.wake_word = None
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_config(self, config_path):
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            print(f"Warning: Config file {config_path} not found. Using defaults.")
            return self.get_default_config()
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration."""
        return {
            'vosk': {
                'model_path': './vosk-model-small-en-us-0.15',
                'sample_rate': 16000,
                'chunk_size': 4000
            },
            'piper': {
                'binary_path': '/usr/local/bin/piper',
                'model_path': './piper-voices/en_US-lessac-medium.onnx',
                'config_path': './piper-voices/en_US-lessac-medium.onnx.json',
                'sample_rate': 22050
            },
            'audio': {
                'input_device_index': None,
                'output_device_index': None,
                'channels': 1,
                'format': 'int16'
            },
            'recording': {
                'silence_threshold': 500,
                'silence_duration': 1.5,
                'max_recording_duration': 30
            },
            'wake_word': {
                'model_name': 'hey_jarvis',
                'enabled': True
            }
        }
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n\nShutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def initialize(self):
        """Initialize STT and TTS engines."""
        print("Initializing Voice Demo...")
        print("=" * 60)
        
        # Initialize Vosk STT
        try:
            vosk_config = self.config['vosk']
            self.stt = VoskSTT(
                model_path=vosk_config['model_path'],
                sample_rate=vosk_config['sample_rate'],
                chunk_size=vosk_config['chunk_size']
            )
            print("✓ Vosk STT initialized")
        except Exception as e:
            print(f"✗ Failed to initialize Vosk STT: {e}")
            raise
        
        # Initialize Piper TTS
        try:
            piper_config = self.config['piper']
            self.tts = PiperTTS(
                binary_path=piper_config['binary_path'],
                model_path=piper_config['model_path'],
                config_path=piper_config.get('config_path'),
                sample_rate=piper_config['sample_rate']
            )
            print("✓ Piper TTS initialized")
        except Exception as e:
            print(f"✗ Failed to initialize Piper TTS: {e}")
            print("\nNote: You may need to install Piper TTS separately.")
            print("See README.md for installation instructions.")
            raise
        
        # Initialize Wake Word Detector
        try:
            wake_config = self.config.get('wake_word', {})
            if wake_config.get('enabled', True):
                self.wake_word = WakeWordDetector(
                    model_name=wake_config.get('model_name', 'hey_jarvis'),
                    sample_rate=self.config['vosk']['sample_rate']
                )
                print("✓ Wake word detector initialized")
        except Exception as e:
            print(f"✗ Failed to initialize wake word detector: {e}")
            print("Continuing without wake word detection...")
            self.wake_word = None
        
        print("=" * 60)
        print()
    
    def list_devices(self):
        """List available audio devices."""
        if self.stt:
            self.stt.list_audio_devices()
        if self.tts:
            self.tts.list_audio_devices()
    
    def run_once(self):
        """Run one cycle: record → transcribe → speak."""
        audio_config = self.config['audio']
        recording_config = self.config['recording']
        
        try:
            # Start recording
            self.stt.start_recording(input_device_index=audio_config.get('input_device_index'))
            
            # Transcribe
            text = self.stt.transcribe_stream(
                silence_threshold=recording_config['silence_threshold'],
                silence_duration=recording_config['silence_duration'],
                max_duration=recording_config['max_recording_duration']
            )
            
            # Stop recording
            self.stt.stop_recording()
            
            # Speak if we got text
            if text and text.strip():
                self.tts.speak(
                    text,
                    output_device_index=audio_config.get('output_device_index')
                )
            else:
                print("No text to speak.\n")
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            self.stt.stop_recording()
        except Exception as e:
            print(f"\nError during processing: {e}")
            self.stt.stop_recording()
            raise
    
    def run_loop(self):
        """Run continuous loop."""
        print("\n" + "=" * 60)
        print("Voice Demo - Ready")
        print("=" * 60)
        if self.wake_word:
            print("Wake word detection enabled - waiting for wake word...")
        else:
            print("Wake word detection disabled - Press Ctrl+C to exit")
        print()
        
        while self.running:
            try:
                # Wait for wake word if enabled
                if self.wake_word:
                    print("Waiting for wake word...")
                    if self.wake_word.listen_for_wake_word(
                        input_device_index=self.config['audio'].get('input_device_index')
                    ):
                        # Wake word detected, now transcribe
                        print("Wake word detected! Starting transcription...")
                        self.run_once()
                        print("\nReturning to wake word detection...\n")
                else:
                    # No wake word, just run directly
                    self.run_once()
                    print("\nReady for next input...\n")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                if not self.running:
                    break
    
    def cleanup(self):
        """Clean up resources."""
        if self.wake_word:
            self.wake_word.cleanup()
        if self.stt:
            self.stt.cleanup()
        if self.tts:
            self.tts.cleanup()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='STT/TTS Voice Demo')
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='List available audio devices and exit'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once instead of looping'
    )
    
    args = parser.parse_args()
    
    # Create demo instance
    demo = VoiceDemo(config_path=args.config)
    
    try:
        # Initialize
        demo.initialize()
        
        # List devices if requested
        if args.list_devices:
            demo.list_devices()
            return
        
        # Run
        if args.once:
            # For --once, still wait for wake word if enabled
            if demo.wake_word:
                if demo.wake_word.listen_for_wake_word(
                    input_device_index=demo.config['audio'].get('input_device_index')
                ):
                    demo.run_once()
            else:
                demo.run_once()
        else:
            demo.run_loop()
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
    finally:
        demo.cleanup()


if __name__ == '__main__':
    main()



