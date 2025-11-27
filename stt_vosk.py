"""
Vosk Speech-to-Text Module

Handles real-time speech recognition using Vosk.
"""

import json
import os
import time
import sounddevice as sd
import numpy as np
from vosk import Model, KaldiRecognizer


class VoskSTT:
    def __init__(self, model_path, sample_rate=16000, chunk_size=4000):
        """
        Initialize Vosk STT engine.
        
        Args:
            model_path: Path to Vosk model directory
            sample_rate: Audio sample rate (Vosk requires 16kHz)
            chunk_size: Audio chunk size for processing
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Vosk model not found at: {model_path}")
        
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        
        # Load Vosk model
        print(f"Loading Vosk model from {model_path}...")
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        self.recognizer.SetWords(True)  # Enable word-level timestamps
        
        # Audio stream state
        self.stream = None
        self.audio_queue = []
        self.recording = False
        
    def list_audio_devices(self):
        """List available audio input devices."""
        print("\nAvailable audio input devices:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                default = " (default)" if i == sd.default.device[0] else ""
                print(f"  [{i}] {device['name']} - {device['max_input_channels']} channels{default}")
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback function for audio stream."""
        if status:
            print(f"Audio callback status: {status}")
        if self.recording:
            # Convert float32 to int16 for Vosk
            # Handle both mono and stereo: take first channel if stereo
            if indata.shape[1] > 1:
                audio_data = indata[:, 0]  # Take first channel if stereo
            else:
                audio_data = indata[:, 0]  # Mono
            audio_int16 = (audio_data * 32767).astype(np.int16)
            self.audio_queue.append(audio_int16.tobytes())
    
    def start_recording(self, input_device_index=None):
        """
        Start recording audio stream.
        
        Args:
            input_device_index: Audio device index (None for default)
        """
        if self.stream is not None:
            self.stop_recording()
        
        self.audio_queue = []
        self.recording = True
        
        # Respeaker 2-Mic HAT: 2 channels, 16kHz
        # Use ALSA device name if input_device_index is None (default)
        device = input_device_index if input_device_index is not None else 'hw:seeed2micvoicec,0'
        
        self.stream = sd.InputStream(
            device=device,
            channels=2,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            dtype='float32',
            callback=self._audio_callback
        )
        self.stream.start()
    
    def stop_recording(self):
        """Stop recording audio stream."""
        self.recording = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def transcribe_stream(self, silence_threshold=500, silence_duration=1.5, max_duration=30):
        """
        Transcribe audio stream in real-time.
        
        Args:
            silence_threshold: RMS threshold for silence detection
            silence_duration: Seconds of silence before stopping
            max_duration: Maximum recording duration in seconds
            
        Returns:
            Final transcribed text
        """
        if self.stream is None:
            raise RuntimeError("Recording not started. Call start_recording() first.")
        
        print("\nListening... (speak now)")
        print("-" * 50)
        
        # Reset recognizer for new session
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        self.recognizer.SetWords(True)
        
        last_speech_time = time.time()
        start_time = time.time()
        partial_text = ""
        last_final_text = ""  # Track the last final result we saw
        
        try:
            while True:
                # Check max duration
                if time.time() - start_time > max_duration:
                    print("\n[Max duration reached]")
                    break
                
                # Process audio from queue
                if self.audio_queue:
                    data = self.audio_queue.pop(0)
                    
                    # Calculate RMS for silence detection
                    audio_array = np.frombuffer(data, dtype=np.int16)
                    if len(audio_array) > 0:
                        mean_squared = np.mean(audio_array**2)
                        # Handle edge cases: NaN, negative, or zero values
                        if np.isnan(mean_squared) or mean_squared <= 0:
                            rms = 0.0
                        else:
                            rms = np.sqrt(mean_squared)
                    else:
                        rms = 0.0
                    
                    # Process with Vosk
                    if self.recognizer.AcceptWaveform(data):
                        # Final result
                        result = json.loads(self.recognizer.Result())
                        if 'text' in result and result['text']:
                            print(f"\n[Final] {result['text']}")
                            last_final_text = result['text']  # Store the final result
                            partial_text = result['text']
                            last_speech_time = time.time()
                    else:
                        # Partial result
                        partial = json.loads(self.recognizer.PartialResult())
                        if 'partial' in partial and partial['partial']:
                            # Only print if different from last partial
                            if partial['partial'] != partial_text:
                                print(f"\r[Partial] {partial['partial']:<50}", end='', flush=True)
                                partial_text = partial['partial']
                                last_speech_time = time.time()
                    
                    # Check for silence
                    if rms > silence_threshold:
                        last_speech_time = time.time()
                    elif time.time() - last_speech_time > silence_duration and partial_text:
                        print("\n[Silence detected]")
                        break
                else:
                    # Small sleep to avoid busy waiting
                    time.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\n[Interrupted by user]")
        
        # Get final result - process any remaining audio
        while self.audio_queue:
            data = self.audio_queue.pop(0)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if 'text' in result and result['text']:
                    last_final_text = result['text']  # Update if we get a newer final result
                    partial_text = result['text']
        
        # Use the last final result we saw, or get final result from recognizer
        if last_final_text:
            final_text = last_final_text
        else:
            # Get final result from recognizer as fallback
            final_result = json.loads(self.recognizer.FinalResult())
            final_text = final_result.get('text', '')
            
            # Use partial_text if final is empty but we have partial
            if not final_text and partial_text:
                final_text = partial_text
        
        if final_text:
            print(f"\n{'='*50}")
            print(f"Transcription: {final_text}")
            print(f"{'='*50}\n")
        else:
            print("\nNo speech detected.\n")
        
        return final_text
    
    def transcribe_file(self, audio_file_path):
        """
        Transcribe audio from a file.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        import wave
        
        wf = wave.open(audio_file_path, "rb")
        
        if wf.getnchannels() != 1:
            raise ValueError("Audio file must be mono")
        if wf.getcomptype() != "NONE":
            raise ValueError("Audio file must be uncompressed")
        
        # Reset recognizer
        self.recognizer = KaldiRecognizer(self.model, wf.getframerate())
        self.recognizer.SetWords(True)
        
        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if 'text' in result:
                    results.append(result['text'])
        
        final_result = json.loads(self.recognizer.FinalResult())
        if 'text' in final_result:
            results.append(final_result['text'])
        
        return ' '.join(results)
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_recording()
