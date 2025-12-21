#! /usr/bin/env python
#               dysh      (issue 946)
#
# dysh pipeline for GBT-EDGE-HI 
#
# Usage patterns:
#    ./edge_hi.py --mode 25 --batch --water
#    ./edge_hi.py --mode 25         --water UGC10972
#    ./edge_hi.py --mode 15 --session 1 NGC3815
#    ./edge_hi.py --mode 15 --session 1 NGC3815 --full
#    ./edge_hi.py --mode 15 --batch                               all 2015 galaxies (113)
#    ./edge_hi.py --mode 25 --batch                               all 2025 galaxies (43)
#
# Bugs @todo
#    - do we need plt.show() ???   there's a plt.ion() in dysh somewhere
#
#  -- 2025 data:
#  CPU info (based on OMP_NUM_THREADS=1)
#  Ultra 7 155H :  100% cpu; but large variable system time    180" + 50" = 230"
#  AMD          :  165% cpu; small system time:                230" +  8" =
#  lma          :  156% CPU: small system                      297 +  10" =
#  M4           :  166% CPU: small system                      105 +  10" = 121
#
# ---- 2015 data
# 1172.40user 106.86system 18:19.91elapsed 116%CPU                     P14s
# 1618.99user 3627.52system 1:35:15elapsed    91%CPU   - 2015 data
#
#  NGC2918 is duplicated in both campaigns, but complicated with VLSR in the GPS RFI band
#
# 2015 data:  
# 2025 data:  typical scan has 37 x 2.5sec exposures = 92.5 sec  (both the ON and OFF)  spectral res = 1.2 km/s   187mhz 32768ch
#

import os
import sys
import argparse
import numpy as np
import astropy.units as u
kms = u.km/u.s
from scipy.stats import anderson
from scipy.signal import medfilt

from dysh.util.files import dysh_data
from dysh.fits.sdfitsload import SDFITSLoad
from dysh.fits.gbtfitsload import GBTFITSLoad
from dysh.fits.gbtfitsload import GBTOnline
from dysh.fits.gbtfitsload import GBTOffline

projects    = ['AGBT15B_287', 'AGBT25A_474']     # mode=0 or 1 (if more, the index into this array)
sdfits_data = "/data2/teuben/sdfits/"            # default, unless given via $SDFITS_DATA

# CLI defaults
smooth  = 3
mode    = 15
blorder = 5
ptype   = 'png'

my_help = f"""
   This is the EDGE-HI pipeline. \n
   Currently supporting {projects[0]} (mode=0 or 15) and {projects[1]} (mode=1 or 25)\n
   Make sure $SDFITS_DATA has been set for mode=1.

   Examples
      ./edge_hi.py --mode 25 UGC10972
      ./edge_hi.py --mode 15 NGC3815 
   """

p = argparse.ArgumentParser(description=my_help, formatter_class=argparse.RawTextHelpFormatter)

p.add_argument('gal',                     nargs='?',           help=f'Galaxy, use all if left blank')
p.add_argument('--session', type = int,   default = None,      help=f'Force single session for given galaxy, [all]')
p.add_argument('--mode',    type = int,   default = mode,      help=f'0 or 15->2015 data   1 or 25->2025 data [{mode}]')
p.add_argument('--smooth',  type = int,   default = smooth,    help=f'boxcar smooth size (channels), use 0 to use raw. [{smooth}]')
p.add_argument('--order',   type = int,   default = blorder,   help=f'baseline order fit (use -1 to skip) [{blorder}]')
p.add_argument('--v0',      type = float, default = None,      help=f'Override vlsr as center of galaxy [pars table entry]')
p.add_argument('--dv',      type = float, default = None,      help=f'Override dv for half signal portion  [pars table entry]')
p.add_argument('--dw',      type = float, default = None,      help=f'Override dw for each half baseline [pars table entry]')
p.add_argument('--avechan', type = int,   default = -1,        help=f'Number of channels to average in waterfall fits file [skip]')
p.add_argument('--plot',                  default = ptype,     help=f'Default plotting type [{ptype}]')
p.add_argument('--water',   action="store_true",               help='make waterfall plot')
p.add_argument('--full',    action="store_true",               help='Use full A/B/C data for mode=0')
p.add_argument('--batch',   action="store_true",               help='Batch mode, no interactive plots')
p.add_argument('--busy',    action="store_true",               help='add the busyfit (needs an extra install)')
p.add_argument('--spike',   action="store_true",               help='attempt spike removal')
p.add_argument('--cog',     action="store_false",              help='use vel_cog instead of our vlsr')


args = p.parse_args()

mode    = args.mode
smooth  = args.smooth
ss      = args.session
blorder = args.order
vlsr    = args.v0
dv      = args.dv
dw      = args.dw
avechan = args.avechan
ptype   = args.plot
my_gals = args.gal
Qwater  = args.water
Qfull   = args.full
Qbatch  = args.batch
Qbusy   = args.busy
Qspike  = args.spike
Qcog    = args.cog

print(args)

if Qbatch:
    print("MATPLOTLIB agg batch mode")
    import matplotlib
    matplotlib.use('agg')     # batch mode
else:
    print("MATPLOTLIB default mode")
    import matplotlib.pyplot as plt    

def get_gals(filename = "gals15.pars"):
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
        # print(gal,gals[gal])
    fp.close()
    if True:
        print(f"Using {filename}")
        for k in gals.keys():
            print(k, gals[k])
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
    calibrators = ['3C84', '3C48', '3C273', '3C196', '3C295', '3C286']
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
    print("Be sure to sanitize this list in gals.pars")

def patch_nan(sp):
    idx_nan = np.where(np.isnan(sp.flux))[0]
    nidx = len(idx_nan)
    for idx in idx_nan:
        print('IDX',idx)
        if idx==0: continue
        print(f"PJT: patching a NaN at {idx}")
        sp.data[idx] = 0.5*(sp.data[idx-1] + sp.data[idx+1])
        sp.mask[idx] = False

def patch_spike(sp, clip=None):
    if clip is None:
        sp.data  = medfilt(sp.data, kernel_size=3)
    else:
        # 4 cases:     single spike up
        #              single spike down
        #              spike up/down
        #              spike down/up
        npatchp = 0
        npatchn = 0
        data = sp.data
        for i in range(len(sp.data)-2):
            if 2*data[i]-data[i-1]-data[i+1] > clip:
                sp.data[i] = 0.5*(data[i-1]+data[i+1])
                npatchp = npatchp + 1
            elif 2*data[i]-data[i-1]-data[i+1] < -clip:
                sp.data[i] = 0.5*(data[i-1]+data[i+1])
                npatchn = npatchn + 1
                
        print(f"Patch_Spike on {clip}: {npatchp} {npatchn}")
        
def patch_spike2(sp, n0, n1, clip):
    npatchp = 0
    npatchn = 0
    npatch1 = 0
    npatch2 = 0
    n = len(sp.data)
    d = sp.data
    print("Patch_spike2:",n,n0,n1)
    if False:
        for i in range(n0-1):
            if abs(d[i]-d[i+1]) > clip:
                sp.mask[i] = True            
        for i in range(n-n1,n-1):
            if abs(d[i]-d[i+1]) > clip:
                sp.mask[i] = True
    else:
        p=[]
        last = False
        for i in range(n-1):
            if last:
                last = False
                continue
            if abs(d[i]-d[i+1]) > clip:
                sp.mask[i] = True
                npatch2 = npatch2 + 1
                p.append(i)
                last = True
        print(f"Patch_Spike2 double spike on {clip}: {npatch2} ")
        print(p)
        if False:
            # now search for single peaks
            p=[]
            for i in range(1,n-1):
                if sp.mask[i]:
                    continue
                if abs(d[i+1]+d[i-1] - 2*d[i]) > clip:
                    sp.mask[i] = True
                    npatch1 = npatch1 + 1
                    p.append(i)
                    last = True                
            print(f"Patch_Spike2 single spike on {clip}: {npatch1} ")
            print(p)

def busyfit(sp, gal, rms):
    """
    the busyfit
    """
    cmd = f"busyfit -c 1 2 {gal}.txt -n {rms} -o {gal} -noplot; sleep 2" 
    print("BUSYFIT:  ",cmd)
    os.system(cmd)

def edge2(sdf, gal, sessions, scans, vlsr, dv, dw, mode=1):
    """  reduce multiple, here session and scans are both arrays
    
    mode=0    2015 ON-OFF-ON getsigref style
    mode=1    2025 ON-OFF getps style
    """
    print(f"Working on {gal} {sessions} {scans} {vlsr} {dv} {dw}")

    ns1 = len(sessions)
    ns2 = len(scans)
    if ns1 != ns2:
        print("number of sessions and scans not the same")
        return None

    sp = []                                      # accumulate spectra in this list for later averaging
    if mode == 1:    # 2025 data
        for i in range(ns1):
            sdf1 = sdf[sessions[i]]
            if Qwater:
                scans_tp = []
                for s in scans[i]:
                    scans_tp.append(s)
                    scans_tp.append(s+1)
                print("waterfall",sessions[i],scans_tp)
                sb1 = sdf1.gettp(scan=scans_tp,fdnum=0,plnum=0,ifnum=0)
                sss = sb1.plot(vmax=1e10)
                print(sss)
                sss.savefig(f'{gal}_water_{sessions[i]}.png')
                if avechan > 0:
                    sss.write(f'{gal}_water_{sessions[i]}.fits', avechan)
                #plt.show()
            sp0 = sdf[sessions[i]].getps(scan=scans[i], fdnum=0, ifnum=0, plnum=0).timeaverage()
            sp1 = sdf[sessions[i]].getps(scan=scans[i], fdnum=0, ifnum=0, plnum=1).timeaverage()
            sp.append(sp0)
            sp.append(sp1)
    elif mode == 0:    # 2015 data
        for i in range(ns1):
            sdf1 = sdf[sessions[i]]  # check
            # waterfall?
            if Qwater:
                scans_tp=[]
                for s in scans[i]:
                    scans_tp.append(s)
                    scans_tp.append(s+1)
                    scans_tp.append(s+2)
                sb1 = sdf1.gettp(scan=scans_tp,fdnum=0,plnum=0,ifnum=1)
                sss = sb1.plot(vmax=1e10)
                sss.savefig(f'{gal}_water_{sessions[i]}.png')
                if avechan > 0:
                    sss.write(f'{gal}_water_{sessions[i]}.fits', avechan)        
                #plt.show()
            for s in scans[i]:
                for pl in [0,1]:
                    #  we will try/except since sessions are not a multiple of 3 scans
                    try:
                        sp1 = sdf1.getsigref(scan=s,ref=s+1,fdnum=0,ifnum=1,plnum=pl).timeaverage()
                        sp.append(sp1)
                    except:
                        print(f"Skipping missing scan {s+2} pol {pl}")
                    try:
                        sp2 = sdf1.getsigref(scan=s+2,ref=s+1,fdnum=0,ifnum=1,plnum=pl).timeaverage()
                        sp.append(sp2)
                    except:
                        print(f"Skipping missing scan {s+2} pol {pl}")
                
    if len(sp) == 0:
        print("Did not find any scans")
        return None

    vmin = vlsr-dv-dw
    vmax = vlsr+dv+dw
    gmin = vlsr-dv
    gmax = vlsr+dv

    sp = sp[0].average(sp[1:])    # average all scans
    patch_nan(sp)

    print(f"Looking at {vlsr} from {vmin} to {vmax}")
    spn = sp[vmin*kms:vmax*kms]

    if Qspike:
        spb0 = spn[vmin*kms:gmin*kms]
        spb1 = spn[gmax*kms:vmax*kms]
        rms = min(spb0.stats(roll=2)["rms"], spb1.stats(roll=2)["rms"])
        n0 = len(spb0.data)
        n1 = len(spb1.data)
        patch_spike2(spn, n0, n1, 5*rms.value)

    if blorder >= 0:
        spn.baseline(blorder,exclude=(gmin*kms,gmax*kms))
        spn.baseline(blorder,exclude=(gmin*kms,gmax*kms),remove=True)

    if smooth > 0:
        sps = spn.smooth("box",smooth)
    else:
        sps = spn

    #   flux a simple sum between gmin and gmax
    spg = sps[gmin*kms:gmax*kms]
    ngal = len(spg.flux)
    sumflux = np.nansum(spg.flux)
    deltav = abs(spg.velocity[0]-spg.velocity[1])
    flux = sumflux * deltav
    vlsr2 = np.nansum(spg.flux * spg.velocity) / sumflux
    vlsr3 = np.nansum(sps.flux * sps.velocity) / np.nansum(sps.flux)
    print("PJT:",vlsr,vlsr2,vlsr3)

    spb0 = sps[vmin*kms:gmin*kms]
    spb1 = sps[gmax*kms:vmax*kms]

    rms0_0 = (spb0.stats()['rms']).to("mK")
    rms1_0 = (spb1.stats()['rms']).to("mK")
                    
    rms0_1 = (spb0.stats(roll=1)['rms']).to("mK")
    rms1_1 = (spb1.stats(roll=1)['rms']).to("mK")

    ad1 = spb0.normalness()  # baseline left
    ad2 = spb1.normalness()  # baseline right
    ad3 = spg.normalness()   # galaxy (possibly smoothed)
    ad0 = spn.normalness()   # whole interval

    print(f'rms0: {rms0_0:.1f} {rms0_1:.1f}')
    print(f'rms1: {rms1_0:.1f} {rms1_1:.1f}')

    rms = max(rms0_1,rms1_1)
    Qb = max(rms0_0, rms0_1, rms1_0, rms1_1) / min(rms0_0, rms0_1, rms1_0, rms1_1)

    print(f'Anderson-Darling test: {ad1:.2f}  {ad2:.2f} {ad3:.2} {ad0:.3}      Qb {Qb:.2f}')
                    
    dflux = rms.to("K")*deltav*np.sqrt(ngal)

    pars = {}
    pars['Qb'] = Qb
    pars['flux'] = flux
    pars['dflux'] = dflux
    pars['rms'] = rms
    pars['vlsr2'] = vlsr2
    
    print("VLSR2:",vlsr2)

    # https://dysh.readthedocs.io/en/latest/explanations/cog/index.html
    try:
        if Qcog:
            cog = sps.cog()
        else:
            cog = sps.cog(vc = vlsr * kms)
        print('COG:',cog)
        flux2 = cog['flux']
        w95 = cog['width'][0.95]
        Qa = (cog['flux_r']-cog['flux_b'])/(cog['flux_r']+cog['flux_b'])
        vel_cog = cog['vel'].value
    except:
        cog = {}
        flux2 = 0.0
        w95 = 0.0
        Qa = 0.0
        vel_cog = 0.0
        print('COG:  failed')
    pars['Qa'] = Qa
    pars['w95'] = w95
    pars['vel_cog'] = vel_cog

    # busyfit
    if Qbusy:
        busyfit(sps, gal, rms.to("K").value)

    print(f"{gal:.15s} Flux: {flux.value:.2f} +/- {dflux:.2f}  {flux2:.2f}  w95 {w95:.1f} rms {rms:.2f} Qb {Qb:.2f} Qa {Qa:.2f} nchan {ngal}")


    print('sps.plot(xaxis_unit="km/s")')

    return sp, sps, pars

def spectrum_plot(sp, gal, project, vlsr, dv, dw, pars, label="smooth"):
    """   a more dedicated EDGE plotter, hardcoded units in km/s and mK
    """
    import matplotlib.pyplot as plt

    vel = sp.axis_velocity().value
    sflux = sp.flux.to("mK").value
    #fig=plt.figure(figsize=(8,4))
    fig,ax1 = plt.subplots()
    Qb = pars["Qb"]
    Qa = pars["Qa"]
    w95 = pars["w95"]
    plt.plot(vel,sflux,label=f'w95 {w95:.1f}  Qa={Qa:.2f}')
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
        if i==0:
            ax1.plot(xb,yb, color='black', label=f'rms={rms:.1f} mK  Qb={Qb:.2f}')
        else:
            ax1.plot(xb,yb, color='black')
    if Qbusy:
        try:
            busyfit_file = f"{gal}_output_spectrum.txt"
            # check if file exists
            (ch,col2,col3) = np.loadtxt(busyfit_file).T
            busyfit = sflux - col3*1000    # flux in mK, col3 was in K
            plt.plot(vel,busyfit,label="busyfit", color="red")
        except:
            print("Some failure in busyfit plotting")
    # draw a vlsr line in green
    ax1.plot([vlsr,vlsr],[-rms,+rms],color='green',label=f'vlsr={vlsr} km/s')
    # draw the cog() 'vel' in red
    vel_cog = pars['vel_cog']
    ax1.plot([vel_cog,vel_cog],[rms,3*rms],color='red',label=f'vel_cog={vel_cog:.1f} km/s')    
    #
    plt.text
    plt.xlabel("Velocity (km/s)")
    plt.ylabel("Intensity (mK)")
    plt.title(f'{gal} {project}  Flux: {flux.value:.2f} +/- {dflux:.2f}')
    plt.legend()
    plt.savefig(f"{gal}_{project}.png")
    #plt.show()
    
# deprecate
def g_test(sp, size=10):
    """kanekar test
    Based on mock gaussian spectra, 95% of the gaussian spectra have 1.16 >= g_test >= 0.79. 
    So, a threshold of 0.79 and 1.16 could be a good value for rejecting non gaussian spectra 
    (i.e., a spectrum is non gaussian if 0.79 < g_test < 1.16).
    """
    ratio = sp.smooth("box", size).stats()["rms"] * np.sqrt(size) / sp.stats()["rms"]
    return ratio

# deprecate
def _rms(sp, mode='std'):
    """
    """
    if mode=='std':
        rms=np.sqrt(np.nanmean(dummy**2)) #the rms is the same of the standard deviation, if and only if, the mean of the data is 0, i.e., the data are following a Gaussian distribution
    elif mode=='mad':
        rms=np.nanmedian(np.abs(dummy-np.nanmedian(dummy)))*1.48
    return rms

#%% issue 558 / 682

if False:
    sdf1 = GBTOffline('AGBT15B_287_19') 
    
    if False:
        sdf1['RESTFREQ'] = 1420405751.786

    sp1 = sdf1.gettp(scan=56,ifnum=1,fdnum=0,plnum=0).timeaverage()   
    sp2 = sdf1.gettp(scan=57,ifnum=1,fdnum=0,plnum=0).timeaverage()
    sp = (sp1-sp2)/sp2 * sp1.meta["TSYS"]
    sp.plot(xaxis_unit="km/s")
    
    if hasattr(sp1,"doppler_rest"):
        print("doppler_resr",sp.doppler_rest)
    print("rest_value",sp.rest_value)
    

    sp_s = sp.with_spectral_axis_unit(u.Hz, rest_value = 1.42041e9 * u.Hz, velocity_convention ='radio')

    # why does this not work ???
    sdf1._index['RESTFREQ'] = 1.42041e9
    # coz it's this:
    sdf1['RESTFREQ'] = 1.42041e9    

    sp1 = sdf1.getsigref(scan=56,ref=57,fdnum=0,ifnum=1,plnum=0).timeaverage()

    sdf1.write("test56.fits", overwrite=True, scan=[56,57],ifnum=1,fdnum=0,plnum=0)



    sdf2 = GBTFITSLoad("test56a.fits")
    sdf2._index['RESTFREQ'] = 1.42041e9
    sp2 = sdf2.getsigref(scan=56,ref=57,fdnum=0,ifnum=1,plnum=0).timeaverage()
    sp2.plot(xaxis_unit="km/s")

    sdf2.write("test56a.fits", overwrite=True)    #  this also doesn't write 1.42


    sdf2 = SDFITSLoad("test56.fits")
    sdf2._bintable[0].data["RESTFREQ"] = 1.42041e9
    sdf2.write("test56a.fits", overwrite=True) 

    sdf3 = SDFITSLoad("/home/teuben/GBT/dysh_data/sdfits/AGBT15B_287_19/AGBT15B_287_19.raw.vegas/AGBT15B_287_19.raw.vegas.B.fits")
    sdf3._bintable[0].data["RESTFREQ"] = 1.42041e9
    sdf3.write("EDGE_19.fits", overwrite=True)  # 2.7 GB

    # these do not work
    sdf4 = GBTFITSLoad("AGBT15B_287_19/AGBT15B_287_19.raw.vegas/AGBT15B_287_19.raw.vegas.B.fits")
    sdf4 = GBTFITSLoad("AGBT15B_287_19")
    sdf4 = GBTFITSLoad("AGBT15B_287_19/AGBT15B_287_19.raw.vegas")


#%%

#    sb = sdf1.gettp(scan=[56,57,58,59,60,61,62,63,64],ifnum=1,fdnum=0,plnum=0)


#%%
if False:
    sdf1 = GBTFITSLoad('data/AGBT15B_287_01.fits')
    # 10-18
    sdf1.write('junk15.fits',scan=[10,11,12,13,14,15,16,17,18],ifnum=1,plnum=0,fdnum=0, overwrite=True)
    
    sdf2 = GBTFITSLoad('junk15.fits')
    sb = sdf2.gettp(ifnum=1,plnum=0,fdnum=0)
    sbsb.plot()
    # using roll=1 RMS is in RAW is about 35,420,341
    
    sdf3 = GBTOffline('AGBT25A_474_01')
    sdf3.write('junk25.fits',scan=[8,9,10,11,12,13,14,15,16,17],ifnum=0,plnum=0,fdnum=0, overwrite=True)
    
    sdf4 = GBTFITSLoad('junk25.fits')
    

#%%
Qraw = True
Qraw = False

if False:
    #sdf1 = GBTOffline('AGBT15B_287_19') 
    #sdf1 = GBTFITSLoad("EDGE_19.fits")
    sdf1 = GBTFITSLoad('AGBT15B_287_19.B.fits')
    sdf1.get_summary()


    sp = []
    s0 = 8        # NGC0528   nothing
    s0 = 17      # UGC04054   ~2085
    s0 = 32      # NGC2481    ~2210
    s0 = 41      # NGC2604     2049
    s0 = 56      # NGC2805      1714
    #s0 = 65      # NGC4211N      6414
    s0 = 80      # NGC3057      1509
    for s in [s0, s0+3, s0+6]:
    #for s in [s0, s0+3]:    
       print(f"Working on scan {s} to contain 3 scans and 2 polarizations")
       for pl in [0,1]:            # two polarizations
           if Qraw:
               sp1 = sdf1.gettp(scan=s+0,ifnum=1,fdnum=0,plnum=pl).timeaverage()
               sp2 = sdf1.gettp(scan=s+1,ifnum=1,fdnum=0,plnum=pl).timeaverage()
               sp3 = sdf1.gettp(scan=s+2,ifnum=1,fdnum=0,plnum=pl).timeaverage()
               sp.append((sp1-sp2)/sp2 * sp1.meta["TSYS"])
               sp.append((sp3-sp2)/sp2 * sp3.meta["TSYS"])
           else:
               try:
                   sp1 = sdf1.getsigref(scan=s,ref=s+1,fdnum=0,ifnum=1,plnum=pl).timeaverage()
                   sp.append(sp1)
               except:
                   print(f"Skipping missing scan {s+2} pol {pl}")
               try:
                   sp2 = sdf1.getsigref(scan=s+2,ref=s+1,fdnum=0,ifnum=1,plnum=pl).timeaverage()
                   sp.append(sp2)
               except:
                   print(f"Skipping missing scan {s+2} pol {pl}")

    final_sp = sp[0].average(sp[1:])
    final_sp.plot(xaxis_unit="km/s")


#%%

if False:    
    sdf1 = GBTOffline('AGBT15B_287_41')
    sdf2 = GBTFITSLoad('data/AGBT15B_287_41.B.fits')

#%% 

if __name__ == "__main__":

    if "SDFITS_DATA" not in os.environ:
        print(f"Setting SDFITS_DATA to {sdfits_data}")
        os.environ["SDFITS_DATA"] = sdfits_data
    print("SDFITS_DATA:", os.environ["SDFITS_DATA"])
        
    #      get galaxy parameters
    if mode==0 or mode==15:
        gals = get_gals("gals15.pars")
        mode=0
    elif mode==1 or mode==25:
        gals = get_gals("gals25.pars")
        mode=1

    if my_gals is None:
        my_gals = gals.keys()
    else:
        # only one galaxy
        my_gals = [my_gals]

    project = projects[mode]

    sdf = {}
    if mode==0:
        print("2015 data")
        if ss is None:
            try_sessions = []
            for g in my_gals:
                sessions = gals[g][0]
                for s in sessions:
                    try_sessions.append(s)
            try_sessions = list(set(try_sessions))                    
            print("PJT try_sessions mode=0:",try_sessions)

        else:
            try_sessions = [ss]
        for i in try_sessions:
            session = i
            if Qfull:
                filename = f'AGBT15B_287_{session:02}'
                print("Opening",filename)
                sdf[session] = GBTOffline(filename)
            else:
                #filename = f'{project}/{project}_{session:02}.B.fits'
                #filename = f'data/{project}_{session:02}.B.fits'
                filename = f'data/{project}_{session:02}.fits'
                print(f"# === {filename}")
                sdf[session] = GBTFITSLoad(filename)   # , skipflags=True)
            sdf[session]["RESTFREQ"] = 1420405751.786
            sdf[session].summary()
            print('FLAGS',sdf[session].final_flags)

    elif mode==1:
        # @todo   if galaxy given, only load what we need
        print("2025 data")
        if ss is None:
            try_sessions = []
            for g in my_gals:
                sessions = gals[g][0]
                for s in sessions:
                    try_sessions.append(s)
            try_sessions = list(set(try_sessions))
            print("PJT try_sessions mode=1:",try_sessions)
        else:
            try_sessions = [ss]
            
        for i in try_sessions:
            session = i
            filename  = f'{project}_{session:02}'
            print(f"# === {filename}")
            sdf[session] =  GBTOffline(filename)  # skipflags=True)
            sdf[session].summary()
            print('FLAGS',sdf[session].final_flags)

    ngal = len(my_gals)
    for (gal,i) in zip(my_gals,range(ngal)):
        print(f"{gal}  {i+1}/{ngal}")
        sessions, scans, vlsr1, dv1, dw1 = gals[gal]
        if vlsr is None:  vlsr = vlsr1
        if dv   is None:  dv   = dv1
        if dw   is None:  dw   = dw1
        print("SESSIONS:",sessions)
        if ss is not None and not ss in sessions:
            continue
        sp,sps,pars = edge2(sdf, gal, sessions, scans, vlsr, dv, dw, mode)
        sss = sps.plot(xaxis_unit="km/s")
        sss.savefig(f'{gal}.png')
        #plt.show()
        sps.write(f'{gal}.txt',format="ascii.commented_header",overwrite=True) 
        spectrum_plot(sp, gal, project, vlsr, dv, dw, pars,  "wide")
        spectrum_plot(sps, gal, project, vlsr, dv, dw, pars, "smooth")
        print("Channel spacing:",sps.velocity[1]-sps.velocity[0])
        print("-----------------------------------")


    if not Qbatch:
        ans = input("Enter anything to exit script and close figures")
