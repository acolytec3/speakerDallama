"""
Piper Text-to-Speech Module

Handles text-to-speech conversion using Piper TTS.
"""

import subprocess
import tempfile
import os
import sounddevice as sd
import soundfile as sf


class PiperTTS:
    def __init__(self, binary_path, model_path, config_path=None, sample_rate=22050):
        """
        Initialize Piper TTS engine.
        
        Args:
            binary_path: Path to piper binary
            model_path: Path to Piper model file (.onnx)
            config_path: Path to Piper config file (.json) - optional
            sample_rate: Output sample rate
        """
        if not os.path.exists(binary_path):
            raise FileNotFoundError(f"Piper binary not found at: {binary_path}")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Piper model not found at: {model_path}")
        
        self.binary_path = binary_path
        self.model_path = model_path
        self.config_path = config_path
        self.sample_rate = sample_rate
        
    def synthesize(self, text, output_file=None):
        """
        Synthesize text to speech.
        
        Args:
            text: Text to convert to speech
            output_file: Optional path to save WAV file (if None, uses temp file)
            
        Returns:
            Path to generated WAV file
        """
        if not text or not text.strip():
            return None
        
        # Use temp file if no output specified
        if output_file is None:
            temp_fd, output_file = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
        
        # Build piper command
        cmd = [
            self.binary_path,
            '--model', self.model_path,
            '--output_file', output_file
        ]
        
        if self.config_path:
            cmd.extend(['--config', self.config_path])
        
        # Run piper
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=text)
            
            if process.returncode != 0:
                raise RuntimeError(f"Piper synthesis failed: {stderr}")
            
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                raise RuntimeError("Piper did not generate audio file")
            
            return output_file
        
        except Exception as e:
            if output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass
            raise
    
    def play_audio(self, wav_file, output_device_index=None):
        """
        Play WAV audio file through speaker.
        
        Args:
            wav_file: Path to WAV file
            output_device_index: Audio device index (None for default)
        """
        if not os.path.exists(wav_file):
            raise FileNotFoundError(f"Audio file not found: {wav_file}")
        
        # Load audio file using soundfile
        data, samplerate = sf.read(wav_file)
        
        # Play audio using sounddevice
        sd.play(data, samplerate=samplerate, device=output_device_index)
        sd.wait()  # Wait until playback is finished
    
    def speak(self, text, output_device_index=None, keep_file=False):
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            output_device_index: Audio device index (None for default)
            keep_file: If True, don't delete temp WAV file after playing
            
        Returns:
            Path to generated WAV file (if keep_file=True)
        """
        if not text or not text.strip():
            return None
        
        output_file = None
        try:
            # Synthesize
            output_file = self.synthesize(text)
            
            # Play
            print(f"Speaking: {text}")
            self.play_audio(output_file, output_device_index)
            
            # Cleanup
            if not keep_file and output_file:
                try:
                    os.remove(output_file)
                    output_file = None
                except:
                    pass
            
            return output_file if keep_file else None
        
        except Exception as e:
            if output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass
            raise
    
    def list_audio_devices(self):
        """List available audio output devices."""
        print("\nAvailable audio output devices:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:
                default = " (default)" if i == sd.default.device[1] else ""
                print(f"  [{i}] {device['name']} - {device['max_output_channels']} channels{default}")
    
    def cleanup(self):
        """Clean up resources."""
        # sounddevice doesn't need explicit cleanup
        pass
