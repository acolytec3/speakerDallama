"""
Flite Text-to-Speech Module

Handles text-to-speech conversion using Flite TTS.
Flite is a lightweight, fast TTS engine optimized for embedded systems.
"""

import subprocess
import tempfile
import os
import sounddevice as sd
import soundfile as sf


class FliteTTS:
    def __init__(self, binary_path='flite', voice='slt', sample_rate=16000):
        """
        Initialize Flite TTS engine.
        
        Args:
            binary_path: Path to flite binary (default: 'flite' - assumes in PATH)
            voice: Voice to use (default: 'slt' - slt, rms, awb, kal, kal16, etc.)
            sample_rate: Output sample rate (Flite typically outputs 16kHz)
        """
        self.voice = voice
        self.sample_rate = sample_rate
        
        # Find flite binary
        self.binary_path = self._find_flite_binary(binary_path)
        
        # Verify flite binary exists and is executable
        self._verify_flite()
    
    def _find_flite_binary(self, binary_path):
        """Find flite binary in common locations or PATH."""
        # If binary_path is just 'flite' or not an absolute path, try to find it
        if binary_path == 'flite' or not os.path.isabs(binary_path):
            # Try using 'which' to find flite in PATH first
            try:
                which_result = subprocess.run(
                    ['which', 'flite'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=2
                )
                if which_result.returncode == 0 and which_result.stdout.strip():
                    found_path = which_result.stdout.strip()
                    if os.path.exists(found_path) and os.access(found_path, os.X_OK):
                        return found_path
            except:
                pass
            
            # Try common locations
            common_paths = ['/usr/bin/flite', '/bin/flite', '/usr/local/bin/flite']
            for path in common_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    return path
        
        # Check if the provided absolute path exists
        if os.path.isabs(binary_path):
            if os.path.exists(binary_path) and os.access(binary_path, os.X_OK):
                return binary_path
        
        raise FileNotFoundError(
            f"Flite binary not found at: {binary_path}\n"
            f"Install with: sudo apt-get install flite"
        )
    
    def _verify_flite(self):
        """Verify that flite binary exists and is executable."""
        if not os.path.exists(self.binary_path):
            raise FileNotFoundError(
                f"Flite binary not found at: {self.binary_path}\n"
                f"Install with: sudo apt-get install flite"
            )
        
        if not os.access(self.binary_path, os.X_OK):
            raise RuntimeError(
                f"Flite binary at {self.binary_path} is not executable"
            )
    
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
        
        # Build flite command
        # -t: text to speak
        # -o: output file
        # -voice: voice selection
        cmd = [
            self.binary_path,
            '-t', text,
            '-o', output_file,
            '-voice', self.voice
        ]
        
        # Run flite
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"Flite synthesis failed: {stderr}")
            
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                raise RuntimeError("Flite did not generate audio file")
            
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
        # Flite doesn't need explicit cleanup
        pass

