#! /usr/bin/env dysh
#
# 2015 data:  
# 2025 data:  typical scan has 37 x 2.5sec exposures = 92.5 sec  (both the ON and OFF)  spectral res = 2.5 km/s
#
# timing:   2'33" for 4 sessions
# 201.52user 54.34system 4:55.45elapsed 86%CPU (0avgtext+0avgdata 12967412maxresident)k

import os
import sys
import numpy as np
import astropy.units as u
kms = u.km/u.s
from scipy.stats import anderson

from dysh.util.files import dysh_data
from dysh.fits.gbtfitsload import GBTFITSLoad
from dysh.fits.gbtfitsload import GBTOnline
from dysh.fits.gbtfitsload import GBTOffline

project     = 'AGBT25A_474'                      # or 'AGBT15B_287_19'
sdfits_data = "/home/teuben/EDGE/GBT-EDGE-HI"    # default if not given via $SDFITS_DATA
Qbatch      = True                               # controls matplotlib.use()
Qbusy       = False                              # add the busyfit (needs an extra install)
smooth      = 3                                  # boxcar smooth size (use 0 to skip and use raw)

# hack for interactive work
#Qbatch      = False
#Qbusy       = False
#smooth      = 15

if Qbatch:
    print("MATPLOTLIB agg batch mode")
    import matplotlib
    matplotlib.use('agg')     # batch mode
else:
    print("MATPLOTLIB default mode")

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

# session=6
# sdf = GBTOffline(f'{project}_{session:02}')
# get_pars(sdf,session)                 



# at GBO:     sdf = GBTOnline()
#             sdf = GBTOffline('AGBT25A_474_01')
#  rsync -av  /home/sdfits/AGBT25A_474_??   teuben@lma.astro.umd.edu:/lma1/teuben/GBT
#
# d76:
#  rc dysh5
#  export SDFITS_DATA=/home/teuben/EDGE/GBT-EDGE-HI
#  rsync -av lma:/lma1/teuben/GBT/AGBT25A_474_?? .
#  

def patch_nan(sp):
    idx_nan = np.where(np.isnan(sp.flux))[0]
    nidx = len(idx_nan)
    for idx in idx_nan:
        print('IDX',idx)
        if idx==0: continue
        print(f"PJT: patching a NaN at {idx}")
        sp.data[idx] = 0.5*(sp.data[idx-1] + sp.data[idx+1])
        sp.mask[idx] = False

def busyfit(sp, gal, rms):
    """
    the busyfit
    """
    cmd = f"busyfit -c 1 2 {gal}.txt -n {rms}"    #   -noplot"     # need to add -n {rms}
    print("BUSYFIT:  ",cmd)
    os.system(cmd)
    cmd = f"cp busyfit_output_spectrum.txt {gal}_output_spectrum.txt"
    os.system(cmd)
    
def waterfall(gals, sdf, gal):
    """ plot waterfall(s) for a given galaxy
        gals: input
        sdf:  input
        gal:  input
    """
    if gal in gals:
        sessions, scans, vlsr, dv, dw = gals[gal]
        print(sessions,scans)
        for i in range(len(sessions)):
            smin = scans[i][0]
            smax = scans[i][-1]+1
            print("Session",sessions[i], "scans",smin,smax)
            sb = sdf[sessions[i]].gettp(scan=list(range(smin,smax+1)),ifnum=0, fdnum=0, plnum=0)
            sb.plot()
      
def edge2(sdf, gal, session, scans, vlsr, dv, dw):
    """  reduce multiple, here session and scans are both arrays
    """
    print(f"Working on {gal} {vlsr} {dv} {dw}")
    blorder = 5

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
    patch_nan(sp)
    
    
    vmin = vlsr-dv-dw
    vmax = vlsr+dv+dw
    gmin = vlsr-dv
    gmax = vlsr+dv

    print(f"Looking at {vlsr} from {vmin} to {vmax}")
    spn = sp[vmin*kms:vmax*kms]

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
                    
    rms0_1 = (spb0.stats(roll=1)['rms']/np.sqrt(2)).to("mK")
    rms1_1 = (spb1.stats(roll=1)['rms']/np.sqrt(2)).to("mK")

    ad0 = p_anderson(spb0)
    ad1 = p_anderson(spb1)

    print(f'rms0: {rms0_0:.1f} {rms0_1:.1f}')
    print(f'rms1: {rms1_0:.1f} {rms1_1:.1f}')

    rms = max(rms0_1,rms1_1)
    Qb = max(rms0_0, rms0_1, rms1_0, rms1_1) / min(rms0_0, rms0_1, rms1_0, rms1_1)

    print(f'Anderson-Darling test: {ad0:.2f}  {ad1:.2f}    Qb {Qb:.2f}')
    
                    
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
        cog = sps.cog(vc = vlsr * kms)
        print('COG:',cog)
        flux2 = cog['flux']
        w95 = cog['width'][0.95]
        Qa = (cog['flux_r']-cog['flux_b'])/(cog['flux_r']+cog['flux_b'])
    except:
        cog = {}
        flux2 = 0.0
        w95 = 0.0
        Qa = 0.0
        print('COG:  failed')
    pars['Qa'] = Qa
    pars['w95'] = w95

    # busyfit
    if Qbusy:
        busyfit(sps, gal, rms.to("K").value)

    print(f"{gal:.15s} Flux: {flux.value:.2f} +/- {dflux:.2f}  {flux2:.2f}  w95 {w95:.1f} rms {rms:.2f} Qb {Qb:.2f} Qa {Qa:.2f} nchan {ngal}")


    print('sps.plot(xaxis_unit="km/s")')

    return sp, sps, pars

def spectrum_plot(sp, gal, vlsr, dv, dw, pars):
    """   a more focused plotter, fuck the units
    """
    print("plotting TBD")
    import matplotlib.pyplot as plt

    vel = sp.axis_velocity().value
    sflux = sp.flux.to("mK").value
    fig=plt.figure(figsize=(8,4))
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
    plt.text
    plt.xlabel("Velocity (km/s)")
    plt.ylabel("Intensity (mK)")
    plt.title(f'{gal}  Flux: {flux.value:.2f} +/- {dflux:.2f}')
    plt.legend()
    plt.savefig(f"{gal}_smooth.png")
    
#%%   https://github.com/SJVeronese/nicci-package/

def p_anderson(sp):
    """  The Anderon-Darling test
    """
    anderson_test=anderson(sp.data)
    print("ANDERSON:", anderson_test.statistic)
    if anderson_test.statistic>=.6:
        p=np.exp(1.2937-5.709*anderson_test.statistic+.0186*anderson_test.statistic**2)
    elif anderson_test.statistic>=.34:
        p=np.exp(0.9177-4.279*anderson_test.statistic-1.38*anderson_test.statistic**2)
    elif anderson_test.statistic>=.2:
        p=1-np.exp(-8.318+42.796*anderson_test.statistic-59.938*anderson_test.statistic**2)
    else:
        p=1-np.exp(-13.436+101.14*anderson_test.statistic-223.73*anderson_test.statistic**2) 
        #store the p-value of the test. The p-value gives the probability that the spectrum is gaussian. 
        # If p>0.05, the spectrum can be considered gaussian   
    return p

def g_test(sp, size=10):
    """kanekar test
    Based on mock gaussian spectra, 95% of the gaussian spectra have 1.16 >= g_test >= 0.79. 
    So, a threshold of 0.79 and 1.16 could be a good value for rejecting non gaussian spectra 
    (i.e., a spectrum is non gaussian if 0.79 < g_test < 1.16).
    """
    ratio = sp.smooth("box", size).stats()["rms"] * np.sqrt(size) / sp.stats()["rms"]
    return ratio

def _rms(sp, mode='std'):
    """
    """
    if mode=='std':
        rms=np.sqrt(np.nanmean(dummy**2)) #the rms is the same of the standard deviation, if and only if, the mean of the data is 0, i.e., the data are following a Gaussian distribution
    elif mode=='mad':
        rms=np.nanmedian(np.abs(dummy-np.nanmedian(dummy)))*1.48
    return rms
    
#%%

if False:
    sdf1 = GBTOffline('AGBT15B_287_19') 
    sdf1.get_summary()

    sp = []
    #for s in [56, 59, 62]:         # three triplets
    #for s in [8,11,14]:
    #for s in [17,20,23]:
    s0 = 8
    #s0 = 17
    #s0 = 32
    #s0 = 41
    #s0 = 56
    #s0 = 65
    #s0 = 80
    for s in [s0, s0+3, s0+6]:
    #for s in [s0, s0+3]:    
       print("Working on ",s)
       for pl in [0,1]:            # two polarizations
           sp1 = sdf1.gettp(scan=s+0,ifnum=1,fdnum=0,plnum=pl).timeaverage()
           sp2 = sdf1.gettp(scan=s+1,ifnum=1,fdnum=0,plnum=pl).timeaverage()
           sp3 = sdf1.gettp(scan=s+2,ifnum=1,fdnum=0,plnum=pl).timeaverage()
           sp.append((sp1-sp2)/sp2 * sp1.meta["TSYS"])
           sp.append((sp3-sp2)/sp2 * sp3.meta["TSYS"])

    final_sp = sp[0].average(sp[1:])

    ta_plt = final_sp.plot(xaxis_unit="km/s", xmin=-4000, xmax=-3500, ymin=-0.1, ymax=1.6)

    sb = sdf.gettp(scan=[56,57,58,59,60,61,62,63,64],ifnum=1,fdnum=0,plnum=0)


#%% 

if __name__ == "__main__":

    if "SDFITS_DATA" not in os.environ:
        print(f"Setting SDFITS_DATA to {sdfits_data}")
        os.environ["SDFITS_DATA"] = sdfits_data
        
    #      get galaxy parameters
    gals = get_gals()

    my_gals = gals.keys()
    if len(sys.argv) > 1:
        my_gals = sys.argv[1:]

    
    #  read all data (4 took 6 sec)    
    sdf = {}
    for i in range(7):
        session = i+1
        filename  = f'{project}_{session:02}'
        print(f"# === {filename}")
        sdf[session] =  GBTOffline(filename, skipflags=True)
        sdf[session].summary()



    for gal in my_gals:
        print(gal)
        sessions, scans, vlsr, dv, dw = gals[gal]
        sp,sps,pars = edge2(sdf, gal, sessions, scans, vlsr, dv, dw)    
        sss = sps.plot(xaxis_unit="km/s")
        sps.write(f'{gal}.txt',format="ascii.commented_header",overwrite=True) 
        sss.savefig(f'{gal}.png')
        spectrum_plot(sps, gal, vlsr, dv, dw, pars)
        print("-----------------------------------")
