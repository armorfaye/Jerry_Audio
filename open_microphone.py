import requests
from PIL import Image
import subprocess
import threading
import numpy as np
import wave
import io
from scipy.fft import fft, fftfreq
import os
from fastapi import FastAPI, Request, Response, File, Form, UploadFile
import uvicorn
# from clap import CLAP
import time 

# URL and Constant 
MIC_1 = "http://192.168.1.108:8100/audio"
MIC_2 = "http://192.168.1.108:8200/audio"
MIC_3 = "http://192.168.1.108:8300/audio"
MIC_4 = "http://192.168.1.108:8400/audio"

URL = "http://192.168.90.163:8100/audio"

def save_wav(response):
	if response.content[:4] != b'RIFF':
		print("Invalid WAV file format received")
	else:
		with wave.open(io.BytesIO(response.content), 'rb') as wav_file:
			audio_frames = wav_file.readframes(wav_file.getnframes())
			with wave.open("8888.wav", 'wb') as output_file:
				output_file.setnchannels(wav_file.getnchannels())
				output_file.setsampwidth(wav_file.getsampwidth())
				output_file.setframerate(wav_file.getframerate())
				output_file.writeframes(audio_frames)

		print("WAV file saved as 8888.wav")
	
def send_request_mic_activation(url):
	response = requests.post(url)
	if response.status_code == 200:
		print("Microphone Activation Success")
	else:
		print(f"Failed to receive audio clip. Status code: {response.status_code}")

# Main Execution
def main():
	#Send request for activation of four microphones
	# threads = []
	# urls = [MIC_1, MIC_2, MIC_3, MIC_4]
	# for url in urls:
	# 	thread = threading.Thread(target=send_request_mic_activation, args=(url,))
	# 	threads.append(thread)
	# 	thread.start()

	# for thread in threads:
	# 	thread.join()

	response = requests.post(URL)
	


if __name__ == "__main__":
	main()

