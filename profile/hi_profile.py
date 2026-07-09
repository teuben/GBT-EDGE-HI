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
nrad = 100
nvel = 200

p = argparse.ArgumentParser(description=my_help, formatter_class=argparse.RawTextHelpFormatter)

p.add_argument('--rmax',  type = float, default = rmax,  help=f'Edge of disk [{rmax}]')

p.add_argument('--m',     type = int,   default = m,     help=f'Order of PLEC [{m}]')
p.add_argument('--rm',    type = float, default = rm,    help=f'Scale length of PLEC [{rm}]')

p.add_argument('--n',     type = int,   default = n,     help=f'Order of Brand RC [{n}]')
p.add_argument('--rn',    type = float, default = rn,    help=f'Scale length of Brand RC [{rn}]')

p.add_argument('--inc',   type = float, default = inc,   help=f'Inclination [{inc}]')
p.add_argument('--sigma', type = float, default = sigma, help=f'Velocity dispersion [{sigma}]')
p.add_argument('--nrad',  type = int,   default = nrad,  help=f'Number of radii [{nrad}]')
p.add_argument('--nvel',  type = int,   default = nvel,  help=f'Number of velocities [{nvel}]')
p.add_argument('--cog',   action="store_true",           help=f'Run Curve of Growth')
p.add_argument('--invert', action="store_true",          help=f'Build the Eq.(44) matrix and test NNLS recovery of Sigma(R) on the synthetic model')
p.add_argument('--reg',   type = float, default = 0.0,   help=f'Tikhonov smoothness regularization strength for --invert / --svfile [0.0 = off]')
p.add_argument('--vsys',  type = float, default = 0.0,   help=f'Systemic velocity [0.0]')

p.add_argument('--rvfile', type = str,  default = None,  help='2-column file: R(kpc) Vrot(km/s) -- replaces the model rotation curve')
p.add_argument('--svfile', type = str,  default = None,  help='2-column file: v(km/s) Phi(flux) -- observed spectrum; triggers real-data NNLS inversion for Sigma(R)')


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


def ring_profile(v_array, Vc, sigma_v, vsys=0.0):
    """
    Gaussian-smoothed, edge-on line profile psi(Vobs, Vc) of a single
    homogeneous ring with circular velocity Vc (Equations 42-43 of
    Obreschkow 2009, ApJ 698, 1467). Normalized so that
    trapz(psi, v_array) = 1.

    Vc is the *projected* circular velocity, i.e. Vrot(R) * sin(inclination).
    """
    v_array = np.asarray(v_array, dtype=float)
    dv_ch = v_array[1] - v_array[0]
    dv = v_array - vsys
    psi_tilde = np.zeros_like(v_array)

    if Vc > 0:
        inside = np.abs(dv) < Vc
        psi_tilde[inside] = 1.0 / (np.pi * np.sqrt(Vc**2 - dv[inside]**2))
    else:
        # degenerate ring (Vc=0): all luminosity at v=vsys
        i0 = np.argmin(np.abs(dv))
        psi_tilde[i0] = 1.0 / dv_ch

    if sigma_v > 0:
        hw = max(1, int(4 * sigma_v / dv_ch))
        kx = np.arange(-hw, hw + 1) * dv_ch
        kernel = np.exp(-0.5 * (kx / sigma_v)**2)
        kernel /= kernel.sum()
        psi = np.convolve(psi_tilde, kernel, mode='same')
    else:
        psi = psi_tilde

    norm = np.trapezoid(psi, v_array)
    if norm > 0:
        psi = psi / norm
    return psi


def hi_matrix(v_array, R, Vrot, inc_deg, sigma_v=8.0, vsys=0.0):
    """
    Build the discretized linear operator Matrix (Equation 44) such that

        Phi = Matrix @ Sigma

    where Sigma(R) (the unknown radial HI surface density) is a vector
    of length len(R), and Phi(v) (the global emission-line profile) is a
    vector of length len(v_array). Column j of Matrix is the trapezoidal-
    weighted, inclination-projected, velocity-dispersion-broadened ring
    profile at radius R[j]:

        Matrix[i, j] = R[j] * w[j] * ring_profile(v_array, Vrot[j]*sin(inc), sigma_v)[i]

    with w[j] the trapezoidal quadrature weight of R[j]. The overall
    2*pi/M_HI normalization factor of Equation (44) is dropped, since
    M_HI itself is a linear functional of the unknown Sigma; the recovered
    Sigma is therefore correct up to that same overall scale (arb. units,
    as in hi_profile() above). sigma_v is the fixed gas velocity
    dispersion (a scalar constant, distinct from the unknown Sigma vector).
    """
    inc = np.radians(inc_deg)
    R = np.asarray(R, dtype=float)
    Vrot = np.asarray(Vrot, dtype=float)
    nrad = len(R)
    nvel = len(v_array)

    w = np.zeros(nrad)
    w[1:-1] = (R[2:] - R[:-2]) / 2
    w[0]  = (R[1] - R[0]) / 2
    w[-1] = (R[-1] - R[-2]) / 2

    Matrix = np.zeros((nvel, nrad))
    for j in range(nrad):
        Vc = Vrot[j] * np.sin(inc)
        Matrix[:, j] = R[j] * w[j] * ring_profile(v_array, Vc, sigma_v, vsys=vsys)

    return Matrix


def invert_hi_profile(v_array, R, Vrot, Phi, inc_deg, sigma_v=8.0, vsys=0.0, reg=0.0):
    """
    Recover the radial HI surface density Sigma(R) from an observed
    global profile Phi(v) and a known rotation curve Vrot(R), by solving
    the linear system Phi = Matrix @ Sigma (Equation 44) via non-negative
    least squares.

    Matrix is typically severely ill-conditioned: a global (integrated)
    profile alone underdetermines the fine radial structure of Sigma, so
    plain NNLS tends to return wildly oscillating, non-physical solutions
    that still fit Phi almost exactly. To stabilize this, an optional
    second-derivative Tikhonov smoothness penalty can be added: the system
    is augmented with rows sqrt(reg) * L, where L is the discrete second-
    difference operator on R, and solved as a single non-negative
    least-squares problem (so Sigma remains non-negative even with
    regularization).

    Parameters
    ----------
    reg : float
        Tikhonov smoothness regularization strength. 0 disables it
        (plain NNLS, likely unstable for realistic nrad).

    Returns
    -------
    Sigma_hat : ndarray
        Recovered non-negative surface density at each R.
    Matrix : ndarray
        The (nvel, nrad) forward operator used for the inversion.
    resid : float
        Residual norm ||Matrix @ Sigma_hat - Phi|| (data term only).
    """
    from scipy.optimize import nnls

    Matrix = hi_matrix(v_array, R, Vrot, inc_deg, sigma_v=sigma_v, vsys=vsys)
    Phi = np.asarray(Phi, dtype=float)
    nrad = Matrix.shape[1]

    if reg > 0:
        L = np.zeros((nrad - 2, nrad))
        for i in range(nrad - 2):
            L[i, i]     = 1.0
            L[i, i + 1] = -2.0
            L[i, i + 2] = 1.0
        A = np.vstack([Matrix, np.sqrt(reg) * L])
        b = np.concatenate([Phi, np.zeros(nrad - 2)])
    else:
        A = Matrix
        b = Phi

    Sigma_hat, _ = nnls(A, b)
    resid = np.linalg.norm(Matrix @ Sigma_hat - Phi)
    return Sigma_hat, Matrix, resid

if __name__ == "__main__":

    args = p.parse_args()
    m = args.m
    rm = args.rm
    n = args.n
    rn = args.rn
    rmax = args.rmax
    nrad = args.nrad
    nvel = args.nvel
    Qcog = args.cog
    model_out = -1
    model_in  = -1

    inc_deg = args.inc      # degrees
    sigma_v = args.sigma    # km/s velocity dispersion
    vsys    = args.vsys     # km/s

    # --- Rotation curve: from file (real data) or analytic model ---
    if args.rvfile:
        rv = np.loadtxt(args.rvfile)
        R, Vrot = rv[:, 0], rv[:, 1]
        nrad = len(R)
        rmax = R[-1]
    else:
        R = np.linspace(0, rmax, nrad)                   # kpc
        x = R/rn
        if n < 0:
            Vrot  = 200 * (1 - np.exp(-x))                    # rising-then-flat (km/s)
        else:
            Vrot = 200 * x * (1/3 + 2/3*x**n) ** (-3/2/n)     # Brand curve

    # --- Real-data mode: invert an observed spectrum for Sigma(R) and stop ---
    if args.svfile:
        sv = np.loadtxt(args.svfile)
        v_arr, Phi = sv[:, 0], sv[:, 1]

        Sigma_hat, Matrix, resid = invert_hi_profile(v_arr, R, Vrot, Phi, inc_deg=inc_deg,
                                                       sigma_v=sigma_v, vsys=vsys, reg=args.reg)
        fit = Matrix @ Sigma_hat

        fig, axes = plt.subplots(1, 3, figsize=(13, 4))

        axes[0].plot(R, Vrot)
        axes[0].set_xlabel("R (kpc)")
        axes[0].set_ylabel("V$_{rot}$ (km/s)")
        axes[0].set_title(f"Rotation curve ({args.rvfile})" if args.rvfile else "Rotation curve (model)")

        axes[1].plot(v_arr, Phi, 'k-', lw=2, label="observed")
        axes[1].plot(v_arr, fit, 'r--', label=f"fit (resid={resid:.3g})")
        axes[1].set_xlabel("v (km/s)")
        axes[1].set_ylabel("$\\Phi$ (arb.)")
        axes[1].set_title(f"Fit  (i={inc_deg}°, $\\sigma_v$={sigma_v} km/s, reg={args.reg:g})")
        axes[1].legend()

        axes[2].plot(R, Sigma_hat, color='C1')
        axes[2].set_xlabel("R (kpc)")
        axes[2].set_ylabel("$\\Sigma$ (arb.)")
        axes[2].set_title(f"Recovered $\\Sigma$(R)  (NNLS, reg={args.reg:g})")

        plt.tight_layout()
        plt.savefig("hi_profile_invert_data.png", dpi=150)
        plt.show()

        np.savetxt("hi_profile_invert_data.tab", np.column_stack([R, Sigma_hat]),
                   header="Radius Sigma_recovered", fmt="%.6g")

        sys.exit(0)

    # --- Synthetic demo: analytic Sigma(R) forward-modeled through Eq.(44) ---
    y = R/rm
    Sigma = y**m * np.exp(-y)

    #v_arr = np.linspace(700, 1300, nvel)
    v_arr = np.linspace(-300, 300, nvel)
    S = hi_profile(v_arr, R, Sigma, Vrot, inc_deg=inc_deg, vsys=vsys, sigma_v=sigma_v)

    # --- Plot ---
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    axes[0].plot(R, Vrot)
    axes[0].set_xlabel("R (kpc)")
    axes[0].set_ylabel("V$_{rot}$ (km/s)")
    axes[0].set_title(f"Rotation Curve  (rn={rn} n={n})")

    axes[1].plot(R, Sigma)
    #axes[1].set_ylim([0,1])
    axes[1].set_xlabel("R (kpc)")
    axes[1].set_ylabel("Surface Brightness (arb.)")
    axes[1].set_title(f"Surface Brightness (rm={rm} m={m})")

    axes[2].plot(v_arr, S)
    axes[2].axvline(vsys, color='gray', linestyle='--', label='v$_{sys}$')
    axes[2].set_xlabel("v (km/s)")
    axes[2].set_ylabel("S (arb.)")
    axes[2].set_title(f"Global HI Profile  (i={inc_deg}°, $\\sigma_v$={sigma_v} km/s)")
    axes[2].legend()

    plt.tight_layout()
    plt.savefig("hi_profile.png", dpi=150)
    plt.show()

    vmask = np.where(v_arr >= 0)

    np.savetxt("hi_profile_sv.tab", np.column_stack([v_arr, S]),
               header="velocity(km/s)  flux(arb)", fmt="%.4f")
    
    np.savetxt("hi_profile_sv0.tab", np.column_stack([v_arr[vmask], S[vmask]]),
               header="velocity(km/s)  flux(arb)", fmt="%.4f")
    
    np.savetxt("hi_profile_rdv.tab", np.column_stack([R, Sigma, Vrot]),
               header="Radius Density Velocity", fmt="%.4f")

    np.savetxt("hi_profile_rv.tab", np.column_stack([R, Vrot]),
               header="Radius Velocity", fmt="%.4f")

    if Qcog:
        # needs NEMO
        os.system("tabcog hi_profile.tab")

    if args.invert:
        # Synthetic test of the Eq.(44) matrix formulation: forward-model
        # Phi = Matrix @ Sigma from the known Sigma/Vrot above, then invert
        # Phi back to Sigma_hat via NNLS and compare to the true Sigma.
        Matrix = hi_matrix(v_arr, R, Vrot, inc_deg=inc_deg, sigma_v=sigma_v, vsys=vsys)
        Phi = Matrix @ Sigma
        Sigma_hat, _, resid = invert_hi_profile(v_arr, R, Vrot, Phi, inc_deg=inc_deg,
                                                 sigma_v=sigma_v, vsys=vsys, reg=args.reg)

        fig2, axes2 = plt.subplots(1, 2, figsize=(9, 4))

        axes2[0].plot(v_arr, Phi)
        axes2[0].set_xlabel("v (km/s)")
        axes2[0].set_ylabel("$\\Phi$ (arb.)")
        axes2[0].set_title("Matrix forward model (Eq. 44)")

        axes2[1].plot(R, Sigma, label="$\\Sigma$ true")
        axes2[1].plot(R, Sigma_hat, '--', label="$\\Sigma$ recovered (NNLS)")
        axes2[1].set_xlabel("R (kpc)")
        axes2[1].set_ylabel("$\\Sigma$ (arb.)")
        axes2[1].set_title(f"NNLS inversion (residual={resid:.3g})")
        axes2[1].legend()

        plt.tight_layout()
        plt.savefig("hi_profile_invert.png", dpi=150)
        plt.show()

