from scipy.fft import fft, fftfreq
import numpy as np
import matplotlib.pyplot as plt
# Number of sample points
N = 600
# sample spacing
T = 1.0 / 800.0


x = np.linspace(0.0, N*T, N, endpoint=False)
y = np.sin(50.0 * 2.0*np.pi*x) + 0.5*np.sin(80.0 * 2.0*np.pi*x) + 0.3*np.sin(0.0 * 2.0*np.pi*x)
yf = fft(y)
xf = fftfreq(N, T)[:N//2]
yf_coeff = 2.0/N * np.abs(yf[0:N//2])

plt.plot(xf, yf_coeff)
plt.grid()
plt.show()