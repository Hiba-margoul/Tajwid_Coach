import noisereduce as nr
import soundfile as sf

data, rate = sf.read("output.wav")
reduced_noise = nr.reduce_noise(y=data, sr=rate)

sf.write("clean_recitation.wav", reduced_noise, rate)