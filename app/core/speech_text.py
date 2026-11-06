import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import keyboard
import time
import threading
import os
#whisper requires ffmpeg
import whisper

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

# Local Whisper transcription (no API key needed).
_model = None

def transcribe(audio_path):
    global _model
    if _model is None:
        _model = whisper.load_model("base")  # Choose model here: https://pypi.org/project/openai-whisper/
    result = _model.transcribe(audio_path)
    return result["text"]

# Recording
fs = 16000
channels = 1
dtype = 'int16'
device = 1  # adjust to your mic
#sd.query_devices()
recording = []
seconds = 0
is_recording = False
running = True

def count_seconds():
    global seconds, is_recording
    seconds = 0
    while is_recording:
        time.sleep(1)
        seconds += 1
        print(f"🎙️ Recording... {seconds} sec", end='\r')

def record_audio():
    global recording, is_recording
    temp = []

    def callback(indata, frames, time_info, status):
        if is_recording:
            temp.append(indata.copy())

    with sd.InputStream(samplerate=fs, channels=channels, dtype=dtype, callback=callback, device=device):
        while is_recording:
            time.sleep(0.1)

    if temp:
        recording = np.concatenate(temp, axis=0)


def cli_reco_transcribe ():
    
    global recording, is_recording
    running = True
    try:
        while running == True:
            
            print("Hold SPACE to record. Press 'q' to quit", end='\r')
            # Break the loop if "q" is pressed
            if keyboard.is_pressed("q"):
                print("\n👋 Quit key detected. Exiting...")
                running = False
                break
            
            if keyboard.is_pressed("space"):
                is_recording = True                                                     
                print("\n")
                # Start both threads
                t1 = threading.Thread(target=record_audio)
                t2 = threading.Thread(target=count_seconds)
                t1.start()
                t2.start()
    
                # Wait until space is released
                while keyboard.is_pressed("space"):                                   
                    time.sleep(0.1)
                    
                is_recording = False
                t1.join()
                t2.join()
                
                print(f"\nRecording finished. Duration: {seconds} seconds.")
                if recording.size > 0:
                    write("recording.wav", fs, recording)
                    print("Saved to recording.wav ✅\n")
                    print(transcribe("recording.wav"))
                else:
                    print("\nNo audio recorded.")
                #break  # Remove this break if you want to do multiple recordings
            time.sleep(0.2)
                
        
    except KeyboardInterrupt:
        print("\nRecording interrupted manually.")
        
    

if __name__ == '__main__':
    cli_reco_transcribe()
