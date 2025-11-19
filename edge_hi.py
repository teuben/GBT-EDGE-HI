#! /usr/bin/env dysh
#
# typical scan has 37 x 2.5sec exposures = 92.5 sec  (both the ON and OFF)
# spectral res = 2.5 km/s
#
# timing:   2'33" for 4 sessions
# 134.69user 6.54system 2:19.69elapsed 101%CPU (0avgtext+0avgdata 6472744maxresident)k
# 132.94user 5.34system 2:16.51elapsed 101%CPU (0avgtext+0avgdata 9641020maxresident)k
# 130.04user 4.62system 2:12.81elapsed 101%CPU (0avgtext+0avgdata 9818976maxresident)k

import sys
import astropy.units as u
import matplotlib
matplotlib.use('agg')     # batch mode

kms     = u.km/u.s
project = 'AGBT25A_474'


def get_gals(filename = "gals.pars"):
    """ reads galaxy parameters. Currently:
    gal       name
    session   1,2,...
    scans     comma separated list of the ON's
    vlsr      km/s
    dv        half the width (km/s)
    dw        width of each baseline section (km/s)
    """
    fp = open(filename)
    gals = {}
    for line in fp.readlines():
        if line[0] == '#': continue
        w = line.split()
        if len(w) < 6:  continue
        gal = w[0]
        session = int(w[1])
        scans = [int(x) for x in w[2].split(',')]
        vlsr = float(w[3])
        dv = float(w[4])
        dw = float(w[5])
        if gal not in gals:
            gals[gal] = ([session],[scans],vlsr,dv,dw)
        else:
            gals[gal][0].append(session)
            gals[gal][1].append(scans)
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
    calibrators = ['3C84', '3C48', '3C273', '3C196', '3C295']
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

# session=6
# sdf = GBTOffline(f'{project}_{session:02}')
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
    """  reduce single
    """
    print(f"Working on {gal} {vlsr} {dv} {dw}")
    
    if sdf == None:
        filename = f'{project}_{session:02}'
        sdf = GBTOffline(filename)
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

def edge2(sdf, gal, session, scans, vlsr, dv, dw):
    """  reduce multiple, here session and scans are both arrays
    """
    print(f"Working on {gal} {vlsr} {dv} {dw}")

    ns1 = len(session)
    ns2 = len(scans)
    if ns1 != ns2:
        return None

    sp = []
    for i in range(ns1):
        sp0 = sdf[session[i]].getps(scan=scans[i], fdnum=0, ifnum=0, plnum=0).timeaverage()
        sp1 = sdf[session[i]].getps(scan=scans[i], fdnum=0, ifnum=0, plnum=1).timeaverage()
        sp.append(sp0)
        sp.append(sp1)

    sp = sp[0].average(sp[1:])
    
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

    pars = {}
    pars['Q'] = Q
    pars['flux'] = flux
    pars['dflux'] = dflux
    pars['rms'] = rms


    print('sps.plot(xaxis_unit="km/s")')

    return sp, sps, pars

def spectrum_plot(sp, gal, vlsr, dv, dw, pars):
    """   a more focused plotter, fuck the units
    """
    print("plotting TBD")
    import matplotlib.pyplot as plt

    vel = sp.axis_velocity().value
    flux = sp.flux.to("mK").value
    fig=plt.figure()
    fig.clf()
    fig,ax1 = plt.subplots()
    plt.plot(vel,flux)
    print("PARS:",pars)
    rms = pars["rms"].to("mK").value
    flux = pars["flux"]
    dflux = pars["dflux"]
    boxes = [vlsr-dv-dw,-rms,vlsr-dv,+rms,  vlsr+dv,-rms,vlsr+dv+dw,+rms]
    #
    xb=np.zeros(5)
    yb=np.zeros(5)
    for i in range(len(boxes)//4):
        i0=i*4
        xb[0] = boxes[i0+0]; yb[0] = boxes[i0+1]
        xb[1] = boxes[i0+2]; yb[1] = boxes[i0+1]
        xb[2] = boxes[i0+2]; yb[2] = boxes[i0+3]
        xb[3] = boxes[i0+0]; yb[3] = boxes[i0+3]
        xb[4] = boxes[i0+0]; yb[4] = boxes[i0+1]
        ax1.plot(xb,yb, color='black')
        print('BOX',i,xb,yb)
    plt.xlabel("Velocity (km/s)")
    plt.ylabel("Intensity (mK)")
    plt.title(f'{gal}  rms={rms:.1f} mK   Flux: {flux.value:.2f} +/- {dflux:.2f}')
    plt.savefig(f"{gal}_smooth.png")



#   get galaxy parameters
gals = get_gals()

my_gals = gals.keys()
if len(sys.argv) > 1:
    my_gals = [sys.argv[1]]

#  read all data (4 took 6 sec)    
sdf = {}
for i in range(6):
    session = i+1
    filename  = f'{project}_{session:02}'
    print(f"# === {filename}")
    sdf[session] =  GBTOffline(filename, skipflags=True)
    sdf[session].summary()

    

for gal in my_gals:
    print(gal)
    session, scans, vlsr, dv, dw = gals[gal]
    #sp,sps = edge1(sdf[session], gal, session, scans, vlsr, dv, dw)
    sp,sps,pars = edge2(sdf, gal, session, scans, vlsr, dv, dw)    
    sss = sps.plot(xaxis_unit="km/s")
    sss.savefig(f'{gal}.png')
    spectrum_plot(sps, gal, vlsr, dv, dw, pars)
    sps.write(f'{gal}.txt',format="ascii.commented_header",overwrite=True) 
    print("-----------------------------------")
