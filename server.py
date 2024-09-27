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
from scipy.io import wavfile
# from clap import CLAP
import time 

# URL and Constant 

class recording():
	def __init__(self):
		self.numbers = [0] * 4
	
	def number_increment(self, id):
		self.numbers[id]+=1 
	
mic_record = recording()

# URLs and Constants
PHOTO = "http://192.168.1.108:8100/photo"
BAND =  "http://192.168.1.108:8500/display"
SAMPLE_RATE = 48000
FFT_ARRAYS = [None] * 4
lock = threading.Lock()

def ffterize(y):
	global SAMPLE_RATE
	N = len(y)
	T = 1/SAMPLE_RATE
	yf = fft(y)
	xf = fftfreq(N, T)[:N//2]
	yf_coeff = 2.0/N * np.abs(yf[:N//2])
	return xf, yf_coeff

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

def process_photo(response_content):
	img = Image.open(io.BytesIO(response_content))
	
	size = min(img.size)
	img = img.crop((0, 0, size, size))
	img = img.resize((224, 224))
	
	base_path = "../FNAC_AVL/Test/"
	img.save(os.path.join(base_path, "frames/recording.jpg"))

def calculate_decibel(data):
	# Calculate RMS value
	rms = np.sqrt(np.mean(data**2))
	# Calculate decibel
	if rms > 0:
		db = 20 * np.log10(rms)
	else:
		db = -np.inf
	return db

app = FastAPI()

@app.post("/process_data")
async def process_data(id: int = Form(...), file: UploadFile = File(...)):
	global mic_record
	mic_record.number_increment(id)
	# Save the uploaded .wav file with the name id.wav
	file_location = f"Data/Number {mic_record.numbers[id]} file of Mic {id}.wav"
	
	with open(file_location, "wb") as buffer:
		buffer.write(await file.read())
	
	return Response(status_code = 200, content=f"File saved as {file_location}")
	return {"message": f"File saved as {file_location}"}

# Processing the 2 second clip and run all the control steps
@app.post("/process_data1")
async def process_data1(id: int = Form(...), file: UploadFile = File(...)):
	
	global mic_record, lock, FFT_ARRAYS

	mic_record.number_increment(id)
	file_location = f"Number {mic_record.numbers[id]} file of Mic {id}.wav"
   
	audio_data = await file.read()
	with open(file_location, "wb") as buffer:
		buffer.write(audio_data)

	rate, data = wavfile.read(io.BytesIO(audio_data))  # Read the WAV file

	if len(data.shape) > 1:  # Convert to mono if stereo
		data = np.mean(data, axis=1)
	
	segment_length = int(rate * 0.01) # Calculate segment length for 0.01 seconds (10 ms)
	
	decibel_levels = [calculate_decibel(data[i:i+segment_length]) for i in range(0, len(data), segment_length)] # Calculate decibel levels for each segment
	
	# Check for continuous duration > 0.2 seconds with decibel > 60
	threshold_count = int(0.2 / 0.01)  # Number of segments for 0.2 seconds
	high_decibel_count = 0
	process_audio = False
	
	for db in decibel_levels:
		if db > 60:
			high_decibel_count += 1
			if high_decibel_count >= threshold_count:
				process_audio = True
				break
		else:
			high_decibel_count = 0
	
	if process_audio:
		# Proceed with data preprocessing
		with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
			audio_frames = wav_file.readframes(wav_file.getnframes())
			np_array = np.frombuffer(audio_frames, dtype=np.int16)
			_, yf_coeff = ffterize(np_array)
			with lock:
				FFT_ARRAYS[id] = yf_coeff
		
		with lock:
			if all(array is not None for array in FFT_ARRAYS):
				fft_matrix = np.vstack(FFT_ARRAYS)
				save_wav(audio_frames, "recording.wav")
				save_wav(audio_frames, "../FNAC_AVL/Test/audio/recording.wav")
				direction_response = requests.post("http://192.168.4.141:8300/cnn", data = fft_matrix) #Send request to cnn server to obtain direction
				direction = direction_response.content
				if direction != 0:
					audio_class_response = requests.post("http://192.168.4.141:8100/clap")
					audio_class = audio_class_response.text.strip().strip('"')
					response = requests.post(BAND, data=f"There is a {audio_class} at {direction}.")
					print(f"Posted to wristband: {response.status_code}")
		   
				time.sleep(3)
		   
				response = requests.post(PHOTO) #Receive image response
				if response.status_code == 200:
					process_photo(response.content) #Process photo and save into proper path
				else:
					print(f"Failed to receive photo. Status code: {response.status_code}")
				audio_class_response = requests.post("http://192.168.4.141:8200/localization_map") #Send request to image server to save localization map
				localization_map_path = "../FNAC_AVL/checkpoints/ezvsl_vggss/viz/recording_pred_av_obj.jpg"
				time.sleep(0.5)
				while not os.path.exists(localization_map_path):
					time.sleep(0.1)
				with open(localization_map_path, "rb") as img_file:
					response = requests.post(BAND, files={"file": img_file}) #Send localization map to wristband
				os.remove(localization_map_path)
				time.sleep(3)
				FFT_ARRAYS[:] = [None] * 4
	else:
		print("Audio Volumn is below 60db - unimportant data")
			   
	return Response(status_code=200)

if __name__ == "__main__":
	uvicorn.run(app, host="0.0.0.0", port=8000)

