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
PHOTO = "http://192.168.1.108:8100/photo"
MIC_2 = "http://192.168.1.108:8200/audio"
MIC_3 = "http://192.168.1.108:8300/audio"
MIC_4 = "http://192.168.1.108:8400/audio"
BAND =  "http://192.168.1.108:8500/display"
SAMPLE_RATE = 48000
FFT_ARRAYS = [None] * 4
lock = threading.Lock()

URL = "http://192.168.90.163:8100/audio"

def ffterize(y):
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
	img.save(os.path.join(base_path, "frames/8888.jpg"))

app = FastAPI()

# Processing the 2 second clip and run all the control steps
@app.post("/process_data") 
async def process_data(id: int = Form(...), file: UploadFile = File(...)):

	file_location = f"{id}.wav"
	
	with open(file_location, "wb") as buffer:
		buffer.write(await file.read())
	
	return Response(status_code=200)

	with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
		decibal = 70
		if decibal > 60: 
			audio_frames = wav_file.readframes(wav_file.getnframes())
			np_array = np.frombuffer(audio_frames, dtype=np.int16)
			xf, yf_coeff = ffterize(np_array)

			with lock:
				FFT_ARRAYS[mic_id] = yf_coeff #Save coefficient in FFT array indexed according to microphone id 

	with lock:
		if all(array is not None for array in FFT_ARRAYS):
			fft_matrix = np.vstack(FFT_ARRAYS)
			save_wav(audio_frames, "8888.wav") #Save audio for second model 
			save_wav(audio_frames, "../FNAC_AVL/Test/audio/8888.wav") #Save audio for third model 
			direction = cnn(fft_matrix)  # Pass fft_matrix into CNN Model for Direction

			if direction != 0:  # If output is not yourself speaking direction
				audio_class = CLAP(8888)  # Calculate object class using CLAP Model 
				response = requests.post(BAND, data=f"There is a {audio_class} at {direction}.")
				print(f"Posted to wristband: {response.status_code}")
			
			time.sleep(3)
			
			response = requests.post(PHOTO) #Post to receive photo from camera 1 

			if response.status_code == 200:
				process_photo(response.content)
				command = [
					"python", "../FNAC_AVL/test.py",
					"--test_data_path", "Test/",
					"--test_gt_path", "GroundTruth/",
					"--model_dir", "checkpoints"
					"--experiment_name", "flickr_144k",
					"--testset", "flickr",
					"--alpha", 0.4,
					"--dropout_img", 0.9,
					"--dropout_aud", 0,
					"--save_visualizations"
				]
				
				subprocess.run(command, capture_output=True, text=True) #Run third model to obtain localization map 
				localization_map_path = "../FNAC_AVL/checkpoints/ezvsl_vggss/viz/8888_pred_av_obj.jpg"

				while (os.path.exists(localization_map_path) == False):
					time.sleep(0.1)

				response = requests.post(BAND, files={"file": open(localization_map_path, "rb")}) #Post localization map to wristband 

				os.remove(localization_map_path)

				time.sleep(3)

				# Reset for the next batch	
				FFT_ARRAYS[:] = [None] * 4

			else:
				print(f"Failed to receive photo. Status code: {response.status_code}")		

		  	
		

if __name__ == "__main__":
	uvicorn.run(app, host="0.0.0.0", port=8000)

