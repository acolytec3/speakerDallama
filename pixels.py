"""
LED light pattern like Google Home
Based on respeaker/mic_hat implementation
"""

import time
import threading
try:
    import queue as Queue
except ImportError:
    import Queue as Queue

try:
    import apa102
    APA102_AVAILABLE = True
except ImportError:
    APA102_AVAILABLE = False
    print("Warning: apa102 library not available. LED patterns will be disabled.")
    print("Install with: pip install apa102-pi")


class Pixels:
    PIXELS_N = 3

    def __init__(self):
        # Increased brightness - basis values are RGB multipliers (0-255)
        # Original was too dim (max 48 out of 255)
        self.basis = [0] * 3 * self.PIXELS_N
        self.basis[0] = 50   # Red for LED 0
        self.basis[3] = 50   # Green for LED 1
        self.basis[4] = 50   # Blue for LED 1
        self.basis[7] = 50   # Red for LED 2

        self.colors = [0] * 3 * self.PIXELS_N
        
        if APA102_AVAILABLE:
            try:
                print("Initializing APA102 LEDs...")
                self.dev = apa102.APA102(num_led=self.PIXELS_N)
                print(f"✓ APA102 initialized successfully with {self.PIXELS_N} LEDs")
                # Test write to verify it works
                self._test_leds()
            except Exception as e:
                print(f"✗ Warning: Could not initialize APA102 LEDs: {e}")
                print(f"  Error type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                self.dev = None
        else:
            print("⚠ APA102 library not available - LEDs disabled")
            self.dev = None

        self.next = threading.Event()
        self.queue = Queue.Queue()
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def wakeup(self, direction=0):
        """Show wakeup pattern when wake word is detected."""
        def f():
            self._wakeup(direction)

        self.next.set()
        self.queue.put(f)

    def listen(self):
        """Show listening pattern when transcribing."""
        self.next.set()
        self.queue.put(self._listen)

    def think(self):
        """Show thinking pattern when waiting for LLM response."""
        self.next.set()
        self.queue.put(self._think)

    def speak(self):
        """Show speaking pattern when TTS is active."""
        self.next.set()
        self.queue.put(self._speak)

    def off(self):
        """Turn off all LEDs."""
        self.next.set()
        self.queue.put(self._off)

    def _run(self):
        """Background thread to handle pixel patterns."""
        while True:
            func = self.queue.get()
            func()

    def _wakeup(self, direction=0):
        """Wakeup animation - lights fade in."""
        if not self.dev:
            print("⚠ Wakeup pattern: LEDs not available")
            return
            
        print("💡 Wakeup pattern starting")
        # Increase brightness multiplier from 24 to 10 (so max is 500, clamped to 255)
        for i in range(1, 11):
            colors = [min(255, i * v) for v in self.basis]
            self.write(colors)
            time.sleep(0.02)

        self.colors = colors

    def _listen(self):
        """Listening animation - lights fade in and stay on."""
        if not self.dev:
            print("⚠ Listen pattern: LEDs not available")
            return
            
        print("💡 Listen pattern starting")
        for i in range(1, 11):
            colors = [min(255, i * v) for v in self.basis]
            self.write(colors)
            time.sleep(0.02)

        self.colors = colors

    def _think(self):
        """Thinking animation - lights rotate."""
        if not self.dev:
            print("⚠ Think pattern: LEDs not available")
            return
            
        print("💡 Think pattern starting")
        colors = self.colors
        # If colors are all zero, initialize them
        if sum(colors) == 0:
            colors = [min(255, v) for v in self.basis]

        self.next.clear()
        while not self.next.is_set():
            colors = colors[3:] + colors[:3]
            self.write(colors)
            time.sleep(0.2)

        t = 0.1
        for i in range(0, 5):
            colors = colors[3:] + colors[:3]
            self.write([(v * (4 - i) / 4) for v in colors])
            time.sleep(t)
            t /= 2

        self.colors = colors

    def _speak(self):
        """Speaking animation - lights pulse."""
        if not self.dev:
            print("⚠ Speak pattern: LEDs not available")
            return
            
        print("💡 Speak pattern starting")
        colors = self.colors
        # If colors are all zero, initialize them
        if sum(colors) == 0:
            colors = [min(255, v) for v in self.basis]
        gradient = -1
        position = 24

        self.next.clear()
        while not self.next.is_set():
            position += gradient
            self.write([(v * position / 24) for v in colors])

            if position == 24 or position == 4:
                gradient = -gradient
                time.sleep(0.2)
            else:
                time.sleep(0.01)

        while position > 0:
            position -= 1
            self.write([(v * position / 24) for v in colors])
            time.sleep(0.01)

    def _off(self):
        """Turn off all LEDs."""
        if not self.dev:
            return
            
        self.write([0] * 3 * self.PIXELS_N)
        print("💡 LEDs turned off")

    def _test_leds(self):
        """Test LEDs by briefly lighting them up."""
        if not self.dev:
            return
        try:
            # Light up all LEDs white briefly
            for i in range(self.PIXELS_N):
                self.dev.set_pixel(i, 50, 50, 50)  # Dim white
            self.dev.show()
            time.sleep(0.1)
            # Turn off
            for i in range(self.PIXELS_N):
                self.dev.set_pixel(i, 0, 0, 0)
            self.dev.show()
            print("✓ LED test completed")
        except Exception as e:
            print(f"✗ LED test failed: {e}")
    
    def write(self, colors):
        """Write colors to LEDs."""
        if not self.dev:
            return
            
        try:
            for i in range(self.PIXELS_N):
                r = max(0, min(255, int(colors[3*i])))
                g = max(0, min(255, int(colors[3*i + 1])))
                b = max(0, min(255, int(colors[3*i + 2])))
                self.dev.set_pixel(i, r, g, b)

            self.dev.show()
        except Exception as e:
            # Print error for debugging instead of silently failing
            print(f"Error writing to LEDs: {e}")
            import traceback
            traceback.print_exc()


# Global instance
pixels = Pixels()


if __name__ == '__main__':
    # Test patterns
    while True:
        try:
            pixels.wakeup()
            time.sleep(3)
            pixels.think()
            time.sleep(3)
            pixels.speak()
            time.sleep(3)
            pixels.off()
            time.sleep(3)
        except KeyboardInterrupt:
            break

    pixels.off()
    time.sleep(1)

