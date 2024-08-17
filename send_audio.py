import requests
import numpy as np
from pydub import AudioSegment

def send_audio_stream(file_path):

    # with open(file_path, 'rb') as f:
    #     audio_data = f.read()
        
    audio = AudioSegment.from_mp3(file_path)
    audio = audio.set_frame_rate(48000)  # Ensure the sample rate matches the server expectation
    audio = audio.set_channels(1)  # Ensure mono audio
    audio_data = np.array(audio.get_array_of_samples(), dtype=np.int16).tobytes()
    
    response = requests.post('http://192.168.4.169:80/process_audio', data=audio_data)
    if response.status_code == 1:       
        pass 


send_audio_stream("Test1.mp3")


