#! /usr/bin/env dysh

import os
import sys
import numpy as np

from dysh.util.files import dysh_data
from dysh.fits.sdfitsload import SDFITSLoad
from dysh.fits.gbtfitsload import GBTFITSLoad
from dysh.fits.gbtfitsload import GBTOnline
from dysh.fits.gbtfitsload import GBTOffline

for f in sys.argv[1:]:
    print(f"Working on {f}")   # AGBT15B_287_19.raw.vegas.B.fits
    head, tail = os.path.split(f)
    session = tail[12:14]
    out = tail[:14] + ".B.fits"
    print(f"Writing {out}")
    sdf = SDFITSLoad(f)
    sdf._bintable[0].data["RESTFREQ"] = 1420.405751786e6
    sdf.write(out, overwrite=True)  # 2.7 GB

