import sounddevice as sd
from scipy.io.wavfile import write

# Paramètres d'enregistrement
fs = 16000  # fréquence d’échantillonnage (16 kHz conseillé pour la voix)
seconds = 5  # durée de l’enregistrement en secondes

print("🎙️ Enregistrement en cours...")
recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
sd.wait()  # attend la fin
print("✅ Enregistrement terminé !")

# Sauvegarde en WAV
write("output.wav", fs, recording)
