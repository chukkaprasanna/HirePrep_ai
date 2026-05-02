import cv2
import time
import numpy as np
from PIL import Image
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
from textblob import TextBlob
import os

# ======================================
# SETTINGS
# ======================================
DURATION = 120   # 2 minutes
VIDEO_FILE = "interview_transcript.avi"
AUDIO_FILE = "interview_audio.wav"
COLLAGE_FILE = "interview_collage.jpg"

# ======================================
# RECORD VIDEO + AUDIO
# ======================================

def record_video_audio():

    print("🎥 Recording started... Speak confidently!")

    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(VIDEO_FILE, fourcc, 20.0, (640, 480))

    # Record audio in parallel
    fs = 44100
    audio = sd.rec(int(DURATION * fs), samplerate=fs, channels=1)

    start = time.time()
    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        out.write(frame)
        frames.append(frame.copy())

        cv2.imshow("Interview Recording", frame)

        if time.time() - start > DURATION:
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    sd.wait()  # wait until audio finished

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    write(AUDIO_FILE, fs, audio)
    print("✅ Recording completed!")

    return frames


# ======================================
# TAKE SNAPSHOTS & MAKE COLLAGE
# ======================================

def create_collage(frames):

    total = len(frames)

    indices = [
        0,
        int(total * 0.5),
        int(total * 0.75),
        total - 1
    ]

    snapshots = []
    for i in indices:
        frame_rgb = cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((400, 300))
        snapshots.append(img)

    collage = Image.new("RGB", (800, 600))

    collage.paste(snapshots[0], (0, 0))
    collage.paste(snapshots[1], (400, 0))
    collage.paste(snapshots[2], (0, 300))
    collage.paste(snapshots[3], (400, 300))

    collage.save(COLLAGE_FILE)
    collage.show()

    print("🖼️ Collage Created!")


# ======================================
# SPEECH RECOGNITION
# ======================================

def analyze_speech():

    print("🧠 Analysing Speech...")
    r = sr.Recognizer()

    with sr.AudioFile(AUDIO_FILE) as source:
        audio = r.record(source)

    try:
        text = r.recognize_google(audio)
        print("\n📝 You said:")
        print(text)

        # Sentiment Analysis
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        print("\n📊 Speaking Feedback:")
        print(f"Confidence sentiment score: {polarity}")

        if polarity > 0.2:
            print("👍 Positive & confident tone!")
        elif polarity < -0.2:
            print("⚠ Negative tone detected. Improve positivity.")
        else:
            print("👌 Neutral tone.")

        # Basic feedback
        word_count = len(text.split())
        print(f"Total words spoken: {word_count}")

        if word_count < 50:
            print("⚠ Try to elaborate more.")
        else:
            print("✅ Good content length.")

    except Exception as e:
        print("❌ Speech Recognition Failed:", e)


# ======================================
# MAIN
# ======================================

if __name__ == "__main__":

    frames = record_video_audio()

    create_collage(frames)

    analyze_speech()

    print("\n🎯 Interview Analysis Completed!")