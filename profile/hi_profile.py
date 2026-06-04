#!/usr/bin/env python

import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt

my_help = """
hi_profile.py - Derive a global HI profile from radial surface brightness and rotation curve.


For a thin, inclined circular disk with inclination i and systemic velocity vsys,
the line-of-sight velocity at azimuth phi and radius R is:

    v_los(R, phi) = vsys + V(R) * sin(i) * cos(phi)

The global profile (flux per velocity channel) is:

    S(v) ~ integral [ Sigma(R) * R / sqrt( (V(R)*sin(i))^2 - (v-vsys)^2 ) ] dR

integrated over all R where |v - vsys| <= V(R)*sin(i).
"""

# CLI defaults

rmax = 10
m = 1
rm = 3
n = 1
rn = 3
inc = 60
sigma = 8

p = argparse.ArgumentParser(description=my_help, formatter_class=argparse.RawTextHelpFormatter)

p.add_argument('--rmax',  type = float, default = rmax,  help=f'Edge of disk [{rmax}]')

p.add_argument('--m',     type = int,   default = m,     help=f'Order of PLEC [{m}]')
p.add_argument('--rm',    type = float, default = rm,    help=f'Scale length of PLEC [{rm}]')

p.add_argument('--n',     type = int,   default = n,     help=f'Order of Brand RC [{n}]')
p.add_argument('--rn',    type = float, default = rn,    help=f'Scale length of Brand RC [{rn}]')

p.add_argument('--inc',   type = float, default = inc,   help=f'Inclination [{inc}]')
p.add_argument('--sigma', type = float, default = sigma, help=f'Velocity dispersion [{sigma}]')


def hi_profile(v_array, R, Sigma, Vrot, inc_deg, vsys=0.0, sigma_v=8.0):
    """
    Compute global HI profile by integrating over annuli.

    Parameters
    ----------
    v_array : array_like
        Velocities at which to evaluate profile (km/s).
    R : array_like
        Radii (kpc or arcsec, consistent with Vrot).
    Sigma : array_like
        Surface brightness at each R (arb. units).
    Vrot : array_like
        Rotation velocity at each R (km/s).
    inc_deg : float
        Inclination in degrees (0=face-on, 90=edge-on).
    vsys : float
        Systemic velocity (km/s).
    sigma_v : float
        Velocity dispersion for Gaussian line broadening (km/s).

    Returns
    -------
    S : ndarray
        Flux density profile (arb. units), same length as v_array.
    """
    inc = np.radians(inc_deg)
    v_array = np.asarray(v_array, dtype=float)
    S = np.zeros_like(v_array)

    for i in range(len(R) - 1):
        dR   = R[i+1] - R[i]
        Rm   = 0.5 * (R[i]     + R[i+1])
        Sm   = 0.5 * (Sigma[i] + Sigma[i+1])
        Vm   = 0.5 * (Vrot[i]  + Vrot[i+1])
        Vmax = Vm * np.sin(inc)          # max projected velocity for this ring

        if Vmax <= 0 or Sm <= 0:
            continue

        dv = v_array - vsys
        inside = np.abs(dv) < Vmax
        # Geometric weight: dS/dv ~ Sigma * R * dR / sqrt(Vmax^2 - dv^2)
        S[inside] += Sm * Rm * dR / np.sqrt(Vmax**2 - dv[inside]**2)

    # Convolve with Gaussian to model velocity dispersion / channel width
    if sigma_v > 0:
        dv_ch = v_array[1] - v_array[0]
        hw = int(4 * sigma_v / dv_ch)
        kx = np.arange(-hw, hw + 1) * dv_ch
        kernel = np.exp(-0.5 * (kx / sigma_v)**2)
        kernel /= kernel.sum()
        S = np.convolve(S, kernel, mode='same')

    return S

if __name__ == "__main__":

    args = p.parse_args()
    m = args.m
    rm = args.rm
    n = args.n
    rn = args.rn
    rmax = args.rmax
    
    # --- Define rotation curve and surface brightness profile ---
    R = np.linspace(0, rmax, 500)                   # kpc
    x = R/rn
    y = R/rm
    if n < 0:
        Vrot  = 200 * (1 - np.exp(-x))                    # rising-then-flat (km/s)
    else:
        Vrot = 200 * x * (1/3 + 2/3*x**n) ** (-3/2/n)     # Brand curve
    

    Sigma = y**m * np.exp(-y)

    inc_deg = args.inc    # degrees
    sigma_v = args.sigma     # km/s velocity dispersion
    vsys    = 1000.0   # km/s
    
    v_arr = np.linspace(700, 1300, 400)
    S = hi_profile(v_arr, R, Sigma, Vrot, inc_deg=inc_deg, vsys=vsys, sigma_v=sigma_v)

    # --- Plot ---
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    axes[0].plot(R, Vrot)
    axes[0].set_xlabel("R (kpc)")
    axes[0].set_ylabel("V$_{rot}$ (km/s)")
    axes[0].set_title(f"Rotation Curve  (rn={rn} n={n})")

    axes[1].plot(R, Sigma)
    axes[1].set_xlabel("R (kpc)")
    axes[1].set_ylabel("Surface Brightness (arb.)")
    axes[1].set_title(f"Surface Brightness (rm={rm} m={m})")

    axes[2].plot(v_arr, S)
    axes[2].axvline(vsys, color='gray', linestyle='--', label='v$_{sys}$')
    axes[2].set_xlabel("v (km/s)")
    axes[2].set_ylabel("S (arb.)")
    axes[2].set_title(f"Global HI Profile  (i={inc_deg}°, σ$_v$={sigma_v} km/s)")
    axes[2].legend()

    plt.tight_layout()
    plt.savefig("hi_profile.png", dpi=150)
    plt.show()

    np.savetxt("hi_profile.tab", np.column_stack([v_arr, S]),
               header="velocity(km/s)  flux(arb)", fmt="%.4f")

