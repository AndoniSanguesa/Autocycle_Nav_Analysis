import numpy as np
import matplotlib.pyplot as plt
import heapq
from scipy import interpolate as interp
import time

full_len = 0

def get_interp(xs, ys):
    global full_len, tck
    tck = interp.splprep([xs, ys], s=0.5)[0]
    full_len = (sum(interp.splint(0, 1, tck, full_output=0))) * 2
    return tck


def get_dervs(x, acc=0.000001):
    """Calculates the derivatives of the curve"""
    k = x / full_len
    subs = lambda x: interp.splev(x, tck)
    this_val = subs(k)
    next_val = subs(k + acc)
    return ((this_val[0] - next_val[0]) / acc,
            (this_val[1] - next_val[1]) / acc)


ys, xs = zip(*[(0.000000, 0.000000), (-1.000000, 0.000000), (-2.000000, 0.000000), (-3.000000, 0.000000), (-4.000000, 0.000000), (-5.000000, 0.000000), (-6.000000, 0.000000), (-7.000000, 0.000000), (-8.000000, 0.000000), (-9.000000, 0.000000), (-10.000000, 0.000000), (-11.000000, 0.000000), (-12.000000, 0.000000), (-13.000000, 0.000000), (-14.000000, 0.000000), (-15.000000, 0.000000)])
print(xs, ys)

tck = get_interp(xs, ys)

x_low = -10
x_high = 10
y_low = -20
y_high = 10
for i in range(x_low, x_high):
    plt.plot([i, i], [y_low, y_high], c="black", linewidth=0.5)

for j in range(y_low, y_high):
    plt.plot([x_low, x_high], [j, j], c="black", linewidth=0.5)

plt.xlim(x_low, x_high)
plt.ylim(y_low, y_high)
u = np.linspace(0, 1, 10)
for i in u:
    x, y = interp.splev(i, tck)
    derv = get_dervs(x)
    ang = np.arctan2(derv[1], derv[0])
    print(ang)
    plt.quiver(x, y, np.cos(ang), np.sin(ang), color="purple")
plt.show()

x_low = -10
x_high = 10
y_low = -20
y_high = 10
for i in range(x_low, x_high):
    plt.plot([i, i], [y_low, y_high], c="black", linewidth=0.5)

for j in range(y_low, y_high):
    plt.plot([x_low, x_high], [j, j], c="black", linewidth=0.5)

plt.xlim(x_low, x_high)
plt.ylim(y_low, y_high)

u = np.linspace(0, 1, 10000)
new_xs, new_ys = [], []
for i in u:
    x, y = interp.splev(i, tck)
    new_xs.append(x)
    new_ys.append(y)
plt.plot(new_xs, new_ys, c="purple")
plt.show()