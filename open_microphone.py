


import requests
import threading
import wave
import io
import time

# URLs and Constants
MIC_1 = "http://192.168.139.174:8100/audio1"
MIC_2 = "http://192.168.139.36:8200/audio2"
MIC_3 = "http://192.168.139.243:8300/audio3"
MIC_4 = "http://192.168.139.163:8400/audio4"

URLS = [MIC_1, MIC_2,MIC_3, MIC_4] # ,MIC_3, MIC_4

def save_wav(response, id):
	if response.content[:4] != b'RIFF':
		print(f"Invalid WAV file format received from microphone {id}")
	else:
		with wave.open(io.BytesIO(response.content), 'rb') as wav_file:
			audio_frames = wav_file.readframes(wav_file.getnframes())
			with wave.open(f"mic_{id}.wav", 'wb') as output_file:
				output_file.setnchannels(wav_file.getnchannels())
				output_file.setsampwidth(wav_file.getsampwidth())
				output_file.setframerate(wav_file.getframerate())
				output_file.writeframes(audio_frames)
		print(f"WAV file saved as mic_{id}.wav")

def send_request_and_save(url, id, start_event, completion_event):
	start_event.wait()  # Wait for the signal to start
	try:
		response = requests.post(url)  # Add a timeout
		if response.status_code == 200:
			print(f"Microphone {id} Activation Success")
			save_wav(response, id)
		else:
			print(f"Failed to receive audio clip from microphone {id}. Status code: {response.status_code}")
	except requests.RequestException as e:
		print(f"Error communicating with microphone {id}: {e}")
	finally:
		completion_event.set()  # Signal that this thread has completed

def main():
	while True:
		start_event = threading.Event()
		completion_events = [threading.Event() for _ in range(2)]
		threads = []

		for i, url in enumerate(URLS):
			thread = threading.Thread(target=send_request_and_save, args=(url, i+1, start_event, completion_events[i]))
			threads.append(thread)
			thread.start()

		# Trigger all threads to start simultaneously
		start_event.set()

		# Wait for all threads to complete
		for event in completion_events:
			event.wait()

		print("All microphones have completed. Starting next round...")


if __name__ == "__main__":
	main()