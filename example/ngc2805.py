#! /usr/bin/env python3
#
#   takes about 3 mins to get spectrum
#
#   AGBT15B_287_19 covers 2015-12-11T05:06:08.00 to 2015-12-11T13:46:28.76
#                  i.e. a little over 8.5 hours
#
from dysh.fits.gbtfitsload import GBTOffline

# this relies on a good value for $SDFITS_DATA  (/home/sdfits at GBO)
sdf = GBTOffline('AGBT15B_287_19')    # about 8.5GB, covering 6 galaxies
df = sdf.get_summary()
df.to_markdown('AGBT15B_287_19.md')

# loop over the three ON-OFF-ON triplets, and both polarizations
# 85 integrations per scan
sp = []
for s in [56, 59, 62]:         # three triplets
   print("Working on ",s)
   for pl in [0,1]:            # two polarizations
       sp1 = sdf.gettp(scan=s+0,ifnum=1,fdnum=0,plnum=pl).timeaverage()
       sp2 = sdf.gettp(scan=s+1,ifnum=1,fdnum=0,plnum=pl).timeaverage()
       sp3 = sdf.gettp(scan=s+2,ifnum=1,fdnum=0,plnum=pl).timeaverage()
       sp.append((sp1-sp2)/sp2 * sp1.meta["TSYS"])
       sp.append((sp3-sp2)/sp2 * sp3.meta["TSYS"])

# and average them       
final_sp = sp[0].average(sp[1:])
final_sp[20000:30000].stats(qac=True)
#  '0.020347771462288694 0.009417386409339035 -0.25814777126242 0.19478180068687698'     2-pol

# final plot and save an ascii spectrum (note the full spectrum has rubbish in them)
# NGC2805 is the line around 1.4123 GHz
ta_plt = final_sp.plot(xaxis_unit="km/s", xmin=-4000, xmax=-3500, ymin=-0.1, ymax=1.6)
ta_plt.savefig('ngc2805.png')
final_sp.write('ngc2805.txt',format='ascii.basic',overwrite=True)
