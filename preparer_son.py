from scipy.io.wavfile import write
import sounddevice as sd
import noisereduce as nr
import soundfile as sf
import librosa
import numpy as np
import librosa.display
import matplotlib.pyplot as plt

# Paramètres d'enregistrement
fs = 16000  # fréquence d’échantillonnage (16 kHz conseillé pour la voix)
seconds = 5  # durée de l’enregistrement en secondes

def prepare_son(filename_clean="clean_recitation.wav"):
    """
    Enregistre le son, le nettoie, normalise et extrait les features audio.
    Retourne :
        y_norm : signal audio normalisé
        sr : fréquence d’échantillonnage
        S_db : spectrogramme en dB
        pitches : matrice des hauteurs (pitch)
        magnitudes : intensités correspondantes
        duration : durée totale du son
    """
    print("🎙️ Enregistrement en cours...")
    recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # attend la fin de l'enregistrement
    print("✅ Enregistrement terminé !")

    # Sauvegarde brute
    write("output.wav", fs, recording)

    # Lecture du fichier
    data, rate = sf.read("output.wav")
    
    # Réduction du bruit
    reduced_noise = nr.reduce_noise(y=data, sr=rate)
    
    # Sauvegarde du fichier nettoyé
    sf.write(filename_clean, reduced_noise, rate)

    # Chargement avec librosa et normalisation
    y, sr = librosa.load(filename_clean, sr=fs)
    y_norm = librosa.util.normalize(y)

    # Calcul du spectrogramme
    D = librosa.stft(y_norm)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)

    # Affichage optionnel du spectrogramme
    plt.figure(figsize=(10, 5))
    librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='hz')
    plt.colorbar(format='%+2.0f dB')
    plt.title("Spectrogramme")
    plt.show()

    # Extraction du pitch et des magnitudes
    pitches, magnitudes = librosa.piptrack(y=y_norm, sr=sr)

    # Durée du signal
    duration = librosa.get_duration(y=y_norm, sr=sr)

    return y_norm, sr, S_db, pitches, magnitudes, duration
prepare_son()
