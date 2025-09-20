#! /usr/bin/env python3

from dysh.util.files import dysh_data
from dysh.fits.gbtfitsload import GBTFITSLoad

sdf1 = GBTFITSLoad( dysh_data(test='getps') )
print(sdf1.filename)
sdf1.summary()
