#! /usr/bin/env dysh
#
# typical scan has 37 x 2.5sec exposures = 92.5 sec  (both the ON and OFF)
# spectral res = 2.5 km/s
#
# timing:   2'33" for 4 sessions

import sys
import astropy.units as u

kms = u.km/u.s


def get_gals(filename = "gals.pars"):
    """ reads galaxy parameters. Currently:
    gal
    session   1,2
    scans     comma separated list of the ON's
    vlsr      km/s
    dv        half the width (km/s)
    dw        width of each baseline section (km/s)
    """
    fp = open(filename)
    gals = {}
    for line in fp.readlines():
        w = line.split()
        if len(w) < 6:  continue
        if w[0] == '#': continue
        gal = w[0]
        session = int(w[1])
        scans = [int(x) for x in w[2].split(',')]
        vlsr = float(w[3])
        dv = float(w[4])
        dw = float(w[5])
        gals[gal] = (session,scans,vlsr,dv,dw)
        print(gal,gals[gal])
    fp.close()
    return gals

def get_pars(sdf, session):
    """ get the pars from an sdf summary, do some sanity checks
    'SCAN',      accumulate the PROCSEQ=1 in scans
    'OBJECT',    gal
    'VELOCITY',  vlsr
    'PROC',      "OnOff"
    'PROCSEQN',  1 or 2
    'RESTFREQ',  -
    'DOPFREQ',   -
    '# IF',      1
    '# POL',     2
    '# INT',     37
    '# FEED',    1
    'AZIMUTH',   -
    'ELEVATION'  show min/max
    """
    calibrators = ['3C84', '3C48', '3C273', '3C196']
    df = sdf.get_summary()
    for gal in df['OBJECT'].unique():
        if gal in calibrators: continue
        df1 = df[df['OBJECT'] == gal]
        vlsr = df1['VELOCITY'].unique()
        scans2 = df1['SCAN'].unique()
        scans=[]
        for s in scans2:
            ps = int(df[df['SCAN'] == s]['PROCSEQN'].values[0])
            if ps == 1:
                scans.append(int(s))
        dv = 200
        dw = 800
        print(gal,session,scans,vlsr,dv,dw)
    print("Be sure to sanitize this list")

# get_pars(sdf,session)                 



# at GBO:     sdf = GBTOnline()
#             sdf = GBTOffline('AGBT25A_474_01')
#  rsync -av  /home/sdfits/AGBT25A_474_01   teuben@lma.astro.umd.edu:/lma1/teuben/GBT
#
# d76:
#  rc dysh5
#  export SDFITS_DATA=/home/teuben/EDGE/GBT-EDGE-HI
#  rsync -av lma:/lma1/teuben/GBT/AGBT25A_474_01 .
#  

def edge1(sdf, gal, session, scans, vlsr, dv, dw):
    """  reduce
    """
    print(f"Working on {gal} {vlsr} {dv} {dw}")
    
    if sdf == None:
        sdf = GBTOffline(f'AGBT25A_474_{session}')
        sdf.summary()

    sp0 = sdf.getps(scan=scans, fdnum=0, ifnum=0, plnum=0).timeaverage()
    sp1 = sdf.getps(scan=scans, fdnum=0, ifnum=0, plnum=1).timeaverage()
    sp = sp0.average(sp1)
    
    vmin = vlsr-dv-dw
    vmax = vlsr+dv+dw
    gmin = vlsr-dv
    gmax = vlsr+dv

    print(f"Looking at {vlsr} from {vmin} to {vmax}")
    spn = sp[vmin*kms:vmax*kms]

    spn.baseline(2,exclude=(gmin*kms,gmax*kms))
    spn.baseline(2,exclude=(gmin*kms,gmax*kms),remove=True)

    if True:
        sps = spn.smooth("box",3)
    else:
        sps = spn

    #   flux a simple sum between gmin and gmax
    spg = sps[gmin*kms:gmax*kms]
    ngal = len(spg.flux)
    sumflux = np.nansum(spg.flux)
    deltav = abs(spg.velocity[0]-spg.velocity[1])
    flux = sumflux * deltav

    spb0 = sps[vmin*kms:gmin*kms]
    spb1 = sps[gmax*kms:vmax*kms]

    rms0_0 = (spb0.stats()['rms']).to("mK")
    rms1_0 = (spb1.stats()['rms']).to("mK")
                    
    rms0_1 = (spb0.stats(roll=1)['rms']/np.sqrt(2)).to("mK")
    rms1_1 = (spb1.stats(roll=1)['rms']/np.sqrt(2)).to("mK")

    print(f'rms0: {rms0_0:.1f} {rms0_1:.1f}')
    print(f'rms1: {rms1_0:.1f} {rms1_1:.1f}')

    rms = max(rms0_1,rms1_1)
    Q = max(rms0_0, rms0_1, rms1_0, rms1_1) / min(rms0_0, rms0_1, rms1_0, rms1_1)
                    
    dflux = rms.to("K")*deltav*np.sqrt(ngal)
    print(f"{gal:.10s} Flux: {flux:.2f} +/- {dflux:.2f}   rms {rms:.2f} Q {Q:.2f} nchan {ngal}")


    print('sps.plot(xaxis_unit="km/s")')

    return sp, sps


gals = get_gals()

my_gals = gals.keys()
if len(sys.argv) > 1:
    my_gals = [sys.argv[1]]

old_session = -1
for gal in my_gals:
    print(gal)
    session, scans, vlsr, dv, dw = gals[gal]
    if session != old_session:
        old_session = session
        sdf =  GBTOffline(f'AGBT25A_474_{session:02}')
        sdf.summary()
    sp,sps = edge1(sdf, gal, session, scans, vlsr, dv, dw)
    sss = sps.plot(xaxis_unit="km/s")
    sss.savefig(f'{gal}.png')
    sps.write
    print("-----------------------------------")
