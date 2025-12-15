#! /usr/bin/env python
#
#  In https://github.com/GreenBankObservatory/dysh/issues/682 I mentioned
#  it was complicated (at the time) to patch the RESTFREQ. This script
#  bypasses that for the 2015 data, but only for ifnum=3, thus also cutting
#  I/O by factor 3.
#
#  on lma for 39 conversions:  28.85user 97.22system 2:57.31elapsed 71%CPU
#  on d76 for  1 conversion:    4.61user  9.54system 0:12.85elapsed 110%CPU  (via dysh)
#                               3.81user  3.07system 0:05.44elapsed 126%CPU  (via python)
#  Typical usage:
#
#   ./patch_restfreq.py /lma2/teuben/dysh_data/sdfits/AGBT15B_287/AGBT15B_287_??.raw.vegas/AGBT15B_287_??.raw.vegas.B.fits
#
#  i.e. it needs a full path, since SDFITSLoad doesn't know about $SDFITS_PATH yet
#
import os
import sys
import numpy as np

from dysh.fits.sdfitsload import SDFITSLoad

for f in sys.argv[1:]:
    print(f"Working on {f}")   # AGBT15B_287_19.raw.vegas.B.fits
    head, tail = os.path.split(f)
    session = tail[12:14]
    out = tail[:14] + ".B.fits"
    print(f"Writing {out}")
    sdf = SDFITSLoad(f)
    sdf._bintable[0].data["RESTFREQ"] = 1420.405751786e6
    sdf.write(out, overwrite=True) 

