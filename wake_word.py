"""
Wake Word Detection using OpenWakeWord
"""

import sounddevice as sd
import numpy as np
from openwakeword import Model
from openwakeword import utils


class WakeWordDetector:
    def __init__(self, model_name="hey_jarvis", sample_rate=16000, chunk_size=1280):
        """
        Initialize wake word detector.
        
        Args:
            model_name: Name of the wake word model (default: "hey_jarvis")
            sample_rate: Audio sample rate (16kHz)
            chunk_size: Audio chunk size for processing
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.model_name = model_name
        
        # Download the wake word model if not already present
        print(f"Downloading wake word model: {model_name}...")
        utils.download_models([model_name])
        
        # Initialize OpenWakeWord model
        self.oww_model = Model(wakeword_models=[model_name])
        self.stream = None
        self.detected = False
        
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback function for audio stream."""
        if status:
            print(f"Wake word audio callback status: {status}")
        if self.detected:
            return
        
        # Convert float32 to int16 numpy array
        if indata.shape[1] > 1:
            audio_data = indata[:, 0]  # Take first channel if stereo
        else:
            audio_data = indata[:, 0]
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Predict wake word - openwakeword expects numpy array, not bytes
        try:
            prediction = self.oww_model.predict(audio_int16)
            
            # Check if wake word detected
            # prediction is a dict where keys are model names and values are probabilities
            for mdl in self.oww_model.models.keys():
                if mdl in prediction:
                    prob = prediction[mdl]
                    # Handle both float and array formats
                    if isinstance(prob, (list, np.ndarray)):
                        prob = prob[0] if len(prob) > 0 else 0.0
                    elif isinstance(prob, np.number):
                        # Handle numpy scalar types (float32, float64, etc.)
                        prob = float(prob)
                    elif isinstance(prob, (int, float)):
                        prob = float(prob)
                    
                    if prob > 0.5:  # Threshold for detection
                        print(f"Wake word detected! Confidence: {prob:.2f}")
                        self.detected = True
                        return
        except Exception as e:
            print(f"Error in wake word prediction: {e}")
    
    def listen_for_wake_word(self, input_device_index=None):
        """
        Listen for wake word continuously.
        
        Args:
            input_device_index: Audio device index (None for default)
            
        Returns:
            True when wake word is detected
        """
        self.detected = False
        
        # Use ALSA device name if input_device_index is None
        device = input_device_index if input_device_index is not None else 'hw:seeed2micvoicec,0'
        
        self.stream = sd.InputStream(
            device=device,
            channels=2,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            dtype='float32',
            callback=self._audio_callback
        )
        
        print("Listening for wake word...")
        self.stream.start()
        
        try:
            while not self.detected and self.stream.active:
                sd.sleep(100)  # Check every 100ms
        except KeyboardInterrupt:
            pass
        
        self.stream.stop()
        self.stream.close()
        self.stream = None
        
        return self.detected
    
    def cleanup(self):
        """Clean up resources."""
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

