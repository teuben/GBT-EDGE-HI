#! /usr/bin/env python
#
#  In https://github.com/GreenBankObservatory/dysh/issues/682 I mentioned
#  it was complicated (at the time) to patch the RESTFREQ. This script
#  bypasses that for the 2015 data, but only for ifnum=1, thus also cutting
#  I/O by factor 3.
#
#  on lma for 39 conversions:  28.85user  97.22system  2:57.31elapsed 71%CPU
#  on d76 for  1 conversion:    4.61user   9.54system  0:12.85elapsed 110%CPU  (via dysh)
#                               3.81user   3.07system  0:05.44elapsed 126%CPU  (via python)
#             39              129.38user 952.51system 20:20.59elapsed 88%CPU   
#  Usage:
#
#   ./patch_restfreq.py
#
#

import os
import sys
import numpy as np

from dysh.fits.gbtfitsload import GBTOffline

for s in [1,3,4,5,6,8,9] + list(range(10,42)):
    fni = f"AGBT15B_287_{s:02}"
    fno = f"data/AGBT15B_287_{s:02}.fits"
    print(fni,fno)
    sdf = GBTOffline(fni)
    # sdf['RESTFREQ'] = 1420405751.786
    sdf.write(fno, ifnum=1, overwrite=True, multifile=False)
