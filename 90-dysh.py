print("hello profile dysh")

from dysh.util.files import dysh_data
from dysh.fits.gbtfitsload import GBTFITSLoad
from dysh.fits.gbtfitsload import GBTOnline
from dysh.fits.gbtfitsload import GBTOffline

import pandas as pd
pd.set_option('display.max_row', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

print("From ~/.ipython/profile_dysh/startup/90-dysh.py: added commands dysh_data, GBTFITSLoad, GBTOnline, GBTOffline")

