import requests
import threading
import numpy as np
import wave
import io
from scipy.fft import fft, fftfreq
from clap import Model
import os
import soundfile as sf

# Constants
ESP32_IP_1 = "http://127.0.0.1:8100"
ESP32_IP_2 = "http://127.0.0.1:8200"
URL_1 = f"{ESP32_IP_1}/audio"
URL_2 = f"{ESP32_IP_2}/audio"
SAMPLE_RATE = 48000
FFT_ARRAYS = [None] * 4

# Helper Functions
def ffterize(y):
    N = len(y)
    T = 1/SAMPLE_RATE
    yf = fft(y)
    xf = fftfreq(N, T)[:N//2]
    yf_coeff = 2.0/N * np.abs(yf[:N//2])
    return xf, yf_coeff

def save_wav(audio_data, filename):
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio_data)

# Audio Processing
def process_audio(response_content):
    header = response_content[:8]
    mic1_id, mic2_id = header[0], header[1]
    audio_data_1 = response_content[8:(len(response_content)//2)]
    audio_data_2 = response_content[(len(response_content)//2):]

    for i, audio_data in enumerate([audio_data_1, audio_data_2]):
        try:
            with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                audio_frames = wav_file.readframes(wav_file.getnframes())
                np_array = np.frombuffer(audio_frames, dtype=np.int16)
                xf, yf_coeff = ffterize(np_array)
                FFT_ARRAYS[mic1_id + i - 1] = yf_coeff

                # Save audio for Model 2 and 3 (only for the first microphone)
                if i == 0:
                    save_wav(audio_frames, "8888.wav")
                    save_wav(audio_frames, "../SIRA-SSL/Test/audio/8888.wav")
        except wave.Error:
            print(f"Failed to process audio data from microphone {mic1_id + i}.")

# Network Request
def send_post_request(url):
    response = requests.post(url)
    if response.status_code == 200:
        process_audio(response.content)
    else:
        print(f"Failed to receive audio clip. Status code: {response.status_code}")

# Main Execution
def main():
    # Send requests
    threads = []
    urls = [URL_1, URL_2]
    for url in urls:
        thread = threading.Thread(target=send_post_request, args=(url,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Model 1 Processing - FFT
    valid_fft_arrays = [arr for arr in FFT_ARRAYS if arr is not None]
    fft_matrix = np.vstack(valid_fft_arrays)  
    print("FFT Matrix shape:", fft_matrix.shape)

    # Model 2 Processing - CLAP Model
    audio_class = Model(8888)
    print(audio_class)

    # Model 3 - Already saved in desired path 

if __name__ == "__main__":
    main()