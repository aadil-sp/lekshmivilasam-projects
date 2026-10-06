"""
Sound synthesizer for Cosmic Star Catcher.
Generates retro 8-bit arcade sound effects mathematically using numpy & pygame.
Zero external audio files required!
"""

import math
import numpy as np
import pygame

class SoundManager:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.enabled = False
        self.sounds = {}
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=512)
            self.enabled = True
            self._generate_all_sounds()
        except Exception as e:
            print(f"[SoundFX] Audio init notice (muted): {e}")
            self.enabled = False

    def _make_sound(self, samples):
        """Converts float numpy array (-1.0 to 1.0) into a stereo pygame.mixer.Sound."""
        samples = np.clip(samples, -1.0, 1.0)
        int_samples = (samples * 32767).astype(np.int16)
        stereo_samples = np.column_stack((int_samples, int_samples))
        return pygame.sndarray.make_sound(stereo_samples)

    def _generate_all_sounds(self):
        sr = self.sample_rate
        
        # 1. Jump / Booster Chirp (Frequency sweep upwards)
        duration = 0.12
        t = np.linspace(0, duration, int(sr * duration), False)
        freq = np.linspace(320, 880, len(t))
        wave = np.sin(2 * np.pi * freq * t) * np.linspace(0.8, 0.0, len(t))
        self.sounds["jump"] = self._make_sound(wave)

        # 2. Star Collect Chime (Arpeggio sparkle)
        duration = 0.18
        t = np.linspace(0, duration, int(sr * duration), False)
        f1, f2, f3 = 880, 1320, 1760
        wave = (0.5 * np.sin(2 * np.pi * f1 * t) +
                0.3 * np.sin(2 * np.pi * f2 * t) +
                0.2 * np.sin(2 * np.pi * f3 * t)) * np.linspace(1.0, 0.0, len(t))
        self.sounds["star"] = self._make_sound(wave)

        # 3. Power-up Fanfare (Upward stepped triad)
        duration = 0.35
        t = np.linspace(0, duration, int(sr * duration), False)
        seg = len(t) // 3
        freqs = np.zeros_like(t)
        freqs[:seg] = 523.25   # C5
        freqs[seg:2*seg] = 659.25 # E5
        freqs[2*seg:] = 783.99 # G5
        wave = 0.6 * np.sin(2 * np.pi * freqs * t) * (1 - t / duration)
        self.sounds["powerup"] = self._make_sound(wave)

        # 4. Asteroid Hit / Boom (Low noise burst)
        duration = 0.25
        t = np.linspace(0, duration, int(sr * duration), False)
        noise = np.random.uniform(-1.0, 1.0, len(t))
        envelope = np.exp(-12 * t)
        low_tone = np.sin(2 * np.pi * 90 * t) * envelope
        wave = (0.7 * noise * envelope) + (0.6 * low_tone)
        self.sounds["hit"] = self._make_sound(wave)

        # 5. Shield Deflect / Ping
        duration = 0.15
        t = np.linspace(0, duration, int(sr * duration), False)
        wave = 0.7 * np.sin(2 * np.pi * 1200 * t) * np.exp(-18 * t)
        self.sounds["shield"] = self._make_sound(wave)

        # 6. Game Over (Melancholic slow descending sweep)
        duration = 0.6
        t = np.linspace(0, duration, int(sr * duration), False)
        freq = np.linspace(440, 110, len(t))
        wave = 0.6 * np.sin(2 * np.pi * freq * t) * np.linspace(1.0, 0.0, len(t))
        self.sounds["gameover"] = self._make_sound(wave)

    def play(self, sound_name):
        if not self.enabled:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            snd.set_volume(0.6)
            snd.play()
