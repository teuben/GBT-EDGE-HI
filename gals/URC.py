# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Universal Rotation Curve
#
# Below  $x = R / R_{opt}$   and $y = L/L_*$

# %%
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# %%

# %%
x = np.linspace(0,2,101)


# %%
def c(y):
    return  (0.80 + 0.44*np.log(y)+(0.87*np.exp(-0.4*y))/(0.47+2.25*y**0.4))**0.5


# %%
def v0(y):
    return 200 * y**0.41 / c(y)


# %%
def vdisk2(x,y):
    v = (0.72+0.44*np.log(y)) * 1.97*x**1.22 / (0.61+x**2)**1.43
    return v

def vhalo2(x,y):
    v = 1.6*np.exp(-0.4*y) * x**2 / (x**2 + 2.25*y**0.4)
    return v
    
def urc(x,y):
    return v0(y) * (vdisk2(x,y) + vhalo2(x,y))**0.5


def urc_min(x, y):
    return -urc(x,y)

y = float(sys.argv[1])
vrot = urc(x,y)

print(y,v0(y),urc(1.0,y),urc(2,y), vrot.max())

result = minimize(fun=urc_min, x0=[1.0], args=(y,))
print(result)

plt.figure()
plt.plot(x,vrot)
plt.show()

