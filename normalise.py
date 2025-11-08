import librosa
import numpy as np

y, sr = librosa.load("clean_recitation.wav", sr=16000)
y_norm = librosa.util.normalize(y)
