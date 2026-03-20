import speech_recognition as sr
import sounddevice as sd
import numpy as np

def listen():
    recognizer = sr.Recognizer()

    print("Listening...")

    duration = 7   # seconds (increased to avoid cutting off speech)
    fs = 16000     # sample rate

    # record audio
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    # convert to AudioData
    audio_data = sr.AudioData(recording.tobytes(), fs, 2)

    try:
        # Natively force deep indian dialect recognition
        text = recognizer.recognize_google(audio_data, language="en-IN")
        print("User :", text)
        return text

    except sr.UnknownValueError:
        print("Could not understand")
        return ""

    except sr.RequestError:
        print("API error")
        return ""