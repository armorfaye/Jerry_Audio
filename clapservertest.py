import requests

response = requests.post("http://192.168.4.141:8100/clap")

print(response.text)