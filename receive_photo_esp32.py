import requests
import os 
from PIL import Image
import io
import subprocess

esp32_ip_1 = "http://127.0.0.1:8100"
url = f"{esp32_ip_1}/photo" 

def process_photo(response_content):
	img = Image.open(io.BytesIO(response_content))
	
	size = min(img.size)
	img = img.crop((0, 0, size, size))
	img = img.resize((224, 224))
	
	base_path = "../SIRA-SSL/Test/"
	img.save(os.path.join(base_path, "frames/8888.jpg"))
	img.save(os.path.join(base_path, "flow/flow_x/8888.jpg"))
	img.save(os.path.join(base_path, "flow/flow_y/8888.jpg"))
	return img

response = requests.post(url)

if response.status_code == 200:
	img = process_photo(response.content)

	name = "SIRA_Test"
	testset = "flickr"
	test_data_path = "../SIRA-SSL/Test/"
	gt_path = "../SIRA-SSL/GroundTruth/"
	image_size = 224
	ckpt = "../SIRA-SSL/logs/SIRA_Train/2500data.ckpt"
	
	command = [
		"python3", "../SIRA-SSL/src/test.py",
		"--name", name,
		"--testset", testset,
		"--test_data_path", test_data_path,
		"--image_size", str(image_size),
		"--gt_path", gt_path,
		"--ckpt", ckpt
	]
	
	result = subprocess.run(command, capture_output=True, text=True)
	print(result.stdout)

else:
	print(f"Failed to receive photo. Status code: {response.status_code}")