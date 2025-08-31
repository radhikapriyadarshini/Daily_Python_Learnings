import numpy as np

# Example signal parameters
fs = 1000  # Sampling frequency (Hz)
t = np.arange(0, 1, 1/fs)  # 1 second duration

# Base sinusoidal (50 Hz) + harmonics
signal = np.sin(2 * np.pi * 50 * t) + 0.2*np.sin(2 * np.pi * 150 * t) + 0.1*np.sin(2 * np.pi * 250 * t)

# FFT to get harmonic components
fft_vals = np.fft.fft(signal)
fft_freqs = np.fft.fftfreq(len(t), 1/fs)

# Magnitudes of positive frequencies
positive_freqs = fft_freqs[fft_freqs >= 0]
magnitudes = np.abs(fft_vals[fft_freqs >= 0])

# Fundamental and harmonic powers
fundamental = magnitudes[np.argmax(positive_freqs == 50)]
harmonics = magnitudes[1:]  # Ignore DC

THD = np.sqrt(np.sum(harmonics**2) - fundamental**2) / fundamental * 100

print(f"Total Harmonic Distortion (THD): {THD:.2f}%")
