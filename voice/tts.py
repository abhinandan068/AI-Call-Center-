import pyttsx3

def speak(text):
    print("AI :", text)

    engine = pyttsx3.init()   # 🔥 create fresh engine every time
    engine.setProperty('rate', 170)

    engine.say(text)
    engine.runAndWait()
    engine.stop()