# Running edge_hi.py

In this directory the command

      ./edge_hi.py --help

will remind you how to run the pipeline.

Here is an example how to run an individual galaxy:

      ./edge_hi.py --mode 25 --spike --water UGC10972

but for some experiments you may need an additional `--smooth` parameter (default: 3), and
sometimes `--order` (default: 5).

Experiment with the correct values of the baseline and galaxy sections of the spectrum,
change them with `--v0`, `--dv` and `--dw`. Typically you will find that
`dv ~ w95/2` (maybe little bit more) and `dw ~ 4 * dv`.  Find good values for
v0, dv and dw to get a reliable value for the Flux.

We need to get an idea how robust the error in the flux is depending on the various
parameters we give it. Take the example UGC10972 above: the default flux
is `15.89 +/- 0.22` - but with `Qb=1.17` a bit high. This is obvious from the erratic residuals
along especially the 2nd baseline. Cutting the baseline in half, i.e. `--dw 500`, we now find
the flux to be `16.82 +/- 0.22`. Clearly the systematic error is larger than the random error
based on the rms.

## Output

Although the important parameters are all in the final spectrum (e.g. NGC3815_smooth.png), the full output also contains
some information useful for debugging. Here's a typical output:

```
./edge_hi.py --spike --mode 15 NGC3815
...

NGC3815  1/1
SESSIONS: [1]
Working on NGC3815 [1] [[10, 13, 16]] 3608.0 250.0 1000.0
IDX 0
IDX 8192
PJT: patching a NaN at 8192
IDX 16384
PJT: patching a NaN at 16384
IDX 24576
PJT: patching a NaN at 24576
Looking at 3608.0 from 2358.0 to 4858.0
Patch_spike2: 3881 1553 1552
Patch_Spike2 double spike on 0.036132104915716244: 15 
[2003, 2878, 2922, 2924, 3012, 3014, 3020, 3024, 3026, 3028, 3030, 3129, 3131, 3681, 3683]
PJT: 3608.0 7265.471120623676 km / s 7294.443938244454 km / s

rms0: 4.4 mK 4.3 mK
rms1: 4.3 mK 4.2 mK
Anderson-Darling test: 0.97  nan nan inf      Qb 1.06
VLSR2: 7265.471120623676 km / s

COG: {'flux': <Quantity 17.09286473 K km / s>, 'flux_std': <Quantity 0.4540021 K km / s>,
      'flux_r': <Quantity 7.32245279 K km / s>, 'flux_r_std': <Quantity 0.44771324 K km / s>,
      'flux_b': <Quantity 9.8492454 K km / s>, 'flux_b_std': <Quantity 2.92929878 K km / s>,
      'width': {0.25: <Quantity 90.81915532 km / s>,
                0.65: <Quantity 229.94637199 km / s>,
                0.75: <Quantity 272.45746597 km / s>,
                0.85: <Quantity 318.83320485 km / s>,
                0.95: <Quantity 415.44932754 km / s>},
      'width_std': {0.25: <Quantity 3.96992344 km / s>,
                    0.65: <Quantity 8.06408423 km / s>,
                    0.75: <Quantity 8.19543947 km / s>,
                    0.85: <Quantity 15.78395215 km / s>,
                    0.95: <Quantity 42.71361523 km / s>},
       'A_F': 1.345074618462, 'A_C': 1.0146615098685248, 'C_V': 3.510638297872347,
       'rms': <Quantity 0.00439632 K>,
       'bchan': 456, 'echan': 886,
       'vel': <Quantity 3653.95210261 km / s>, 'vel_std': <Quantity 90.72090395 km / s>,
       'vframe': 'itrs', 'doppler_convention': 'radio'}

NGC3815 Flux: 16.69 +/- 0.13 K km / s  17.09 K km / s  w95 415.4 km / s rms 4.26 mK Qb 1.06 Qa -0.15 nchan 258
sps.plot(xaxis_unit="km/s")


PARS: {'Qb': <Quantity 1.05899967>, 'flux': <Quantity 16.6925696 K km / s>, 'dflux': <Quantity 0.13218292 K km / s>,
'rms': <Quantity 4.25878669 mK>, 'vlsr2': <Quantity 7265.47112062 km / s>, 'Qa': <Quantity -0.14714867>,
'w95': <Quantity 415.44932754 km / s>, 'vel_cog': 3653.9521026095617}

PARS: {'Qb': <Quantity 1.05899967>, 'flux': <Quantity 16.6925696 K km / s>, 'dflux': <Quantity 0.13218292 K km / s>,
'rms': <Quantity 4.25878669 mK>, 'vlsr2': <Quantity 7265.47112062 km / s>, 'Qa': <Quantity -0.14714867>,
'w95': <Quantity 415.44932754 km / s>, 'vel_cog': 3653.9521026095617}

Channel spacing: 1.9323224536647103 km / s

```



## spreadsheet

In the spreadsheet we experiment with different values of the parameters. Defaults come from ``gals15.par`` or ``gals25.par``.
Highlight the row with your preferred/best solution in yellow.

Parameters:

* **Gal**:     Galaxy name
* **VLSR:**    VLSR from the table (km/s)
* **v0:**      overriding value for VLSR. Sometimes to just get the emission to center, and it's not the VLSR actually (km/s)
* **vel_cog:** velocity centroid according to the Curve of Growth (cog) method in dysh (km/s)
* **w95:**     width containing 95% of the emission according to cog  (km/s)
* **dv:**      half the width of the galaxy signal  (km/s)
* **dw:**      width of each of the baseline halves  (km/s)
* **smooth:**  number of channels to (boxcar) smooth the final spectrum [3]
* **Flux:**    Flux  (in K.km/s) 
* **eFlux:**   error in Flux (in K.km/s)
* **rms:**     RMS in the baseline (mK)
* **Qb:**      Quality of the residuals in the baselines (1.0 is perfect)
* **comments:** 
