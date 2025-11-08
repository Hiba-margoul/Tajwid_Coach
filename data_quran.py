import sounddevice as sd
import soundfile as sf

data, fs = sf.read("output.wav", dtype="float32")
sd.play(data, fs)
sd.wait()
