import numpy as np
from scipy.interpolate import UnivariateSpline
import matplotlib.pyplot as plt


x_front = range(-90,91,10)
y_bot = (7.755,7.900,7.980,8.000,8.000,8.000,8.000,8.005,8.005,8.005,8.010,8.010,8.005,8.000,8.005,8.005,8.000,7.910,7.750)

spl = UnivariateSpline(x_front,y_bot, s=0.0)

x2 = np.linspace(-90,90,1000)
plt.plot(x2, spl(x2), 'g', x_front, y_bot, 'd')
plt.show()
