from transformers import ClapModel, AutoProcessor

# Load the pre-trained CLAP model
model = ClapModel.from_pretrained("laion/clap-htsat-unfused")

# Load the processor (which includes both the feature extractor and tokenizer)
processor = AutoProcessor.from_pretrained("laion/clap-htsat-unfused")

import numpy as np
import librosa
import soundfile as sf

# Comparison Text
input_text = [
	"Sound of a Dog",
	"Sound of a Person Talking",
	"Sound of a Car Engine",
	"Sound of a Car Honking",
	"Sound of a Guitar",
	"Sound of a Piano",
	"Sound of a Violin",
	"Sound of a Bike Bell",
	"Sound of an Ambulance or Firetruck Siren",
	"Sound of a Train",
	"Sound of a Phone Ringing",
	"Sound of a Doorbell",
	"Sound of a Microwave Beeping",
	"Sound of a Leaf Blower",
	"Sound of a Helicopter",
]

output_class = [
	"Dog",
	"Person Talking",
	"Car Engine",
	"Car Honking",
	"Guitar",
	"Piano",
	"Violin",
	"Bike Bell",
	"Siren",
	"Train",
	"Phone Ringing",
	"Doorbell",
	"Microwave",
	"Leaf Blower",
	"Helicopter",
]

def spectral_subtraction(input_file, output_file, noise_reduction_factor=1.0, frame_length=2048, hop_length=512):
	y, sr = librosa.load(input_file, sr=None)
	
	# Compute the Short-Time Fourier Transform (STFT) of the audio signal
	stft = librosa.stft(y, n_fft=frame_length, hop_length=hop_length)
	magnitude, phase = np.abs(stft), np.angle(stft)
	
	# Estimate the noise power spectrum from a silent part of the audio (e.g., the first 0.5 seconds)
	noise_frames = magnitude[:, :int(0.5 * sr / hop_length)]
	noise_profile = np.mean(noise_frames, axis=1, keepdims=True)
	
	# Perform spectral subtraction
	magnitude_subtracted = magnitude - noise_reduction_factor * noise_profile
	magnitude_subtracted = np.maximum(magnitude_subtracted, 0)  
	
	stft_subtracted = magnitude_subtracted * np.exp(1j * phase)
	y_denoised = librosa.istft(stft_subtracted, hop_length=hop_length)
	sf.write(output_file, y_denoised, sr)

# input_file = 'BikeBellWithNoise.wav'
# output_file = 'PianoWithoutNoise.wav'
# spectral_subtraction(input_file, output_file)


def CLAP(name):
	input_file = f'{name}.wav'
	audio, orig_sr = librosa.load(input_file, sr=None)
	target_sr = 48000 
	if orig_sr != target_sr: 
		audio = librosa.resample(y=audio, orig_sr = orig_sr, target_sr = target_sr)
	#Process the Audio and the Text 
	inputs = processor(text=input_text, audios=[audio], sampling_rate = 48000, return_tensors="pt", padding=True)
	# Forward pass through the model
	outputs = model(**inputs)
	logits_per_audio = outputs.logits_per_audio 
	probs = logits_per_audio.softmax(dim=-1)
	probs_arr = probs.detach().numpy()
	return output_class[np.argmax(probs_arr)]

print(Model("guitar"))
