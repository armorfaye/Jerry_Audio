from fastapi import FastAPI, Request,Response
from fastapi.responses import JSONResponse
import numpy as np
import asyncio
import uvicorn
import traceback
import sys

from scipy.fft import fft, fftfreq
import numpy as np
import matplotlib.pyplot as plt
import wave

app = FastAPI()

@app.post("/process_audio") 
async def process_audio(request: Request):

    audio_data = await request.body()

    y = np.frombuffer(audio_data, dtype=np.int16)
    
    SAMPLE_RATE = 48000 

    N = len(y)
    T = 1/SAMPLE_RATE
    
    yf = fft(y)
    xf = fftfreq(N, T)[:N//2]
    yf_coeff = 2.0/N * np.abs(yf[:N//2])


    plt.plot(np.linspace(0.0,N*T,N),y)
    plt.grid()
    plt.show()


    plt.plot(xf,yf_coeff)
    plt.grid()
    plt.show()
    
    return Response(status_code=1)

@app.post("/test") 
async def test(request: Request):
    print("1")
    print(request.body())
    return Response(status_code=1)

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=80)
    except Exception as e:
        print("An error occurred while starting the server:")
        traceback.print_exc()
        sys.exit(1)
