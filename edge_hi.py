#! /usr/bin/env python
#               dysh      (issue 946)
#
# dysh pipeline for GBT-EDGE-HI
#    - 2015 data are ON-OFF-ON and use getsigref
#    - 2025 data are ON-OFF and use getps
#    - a velocity frame (default "icrs") is selected for aligning spectra
#    - zenith opacity 0.008 is assumed; default conversion is to Jy
#
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
#    - set the frame can cause spike at n*8192
#
#  -- 2025 data:
#  CPU info (based on OMP_NUM_THREADS=1)
#  Ultra 7 155H :  100% cpu; but large variable system time    180" + 50" = 230"
#  AMD          :  165% cpu; small system time:                230" +  8" =
#  lma          :  156% CPU: small system                      297 +  10" =
#  M4           :  166% CPU: small system                      105 +  10" = 121
#
# ---- 2015 data
# 1172.40user  106.86system   18:19.91elapsed 116%CPU                     P14s
# 1618.99user 3627.52system 1:35:15elapsed    91%CPU   - 2015 data
#
#  NGC2918 is duplicated in both campaigns, but complicated with VLSR in the GPS RFI band
#          plus it seems to have no or little emission
#

import os
import sys
import argparse
import numpy as np
from astropy.stats import mad_std
import astropy.units as u
kms = u.km/u.s
from scipy.stats import anderson
from scipy.signal import medfilt

import dysh
from dysh.util.files import dysh_data
from dysh.fits.sdfitsload import SDFITSLoad
from dysh.fits.gbtfitsload import GBTFITSLoad
from dysh.fits.gbtfitsload import GBTOnline
from dysh.fits.gbtfitsload import GBTOffline

from IPython import embed

projects    = ['AGBT15B_287', 'AGBT25A_474', 'AGBT04A_008', '-']  # mode=0 or 1 (if more, the index into this array)
refcodes    = ['edge2015',    'edge2025',    'survey2004',  '-']  # for CSV output
sdfits_data = "/data2/teuben/sdfits/"                             # default, override with $SDFITS_DATA
version     = "8-apr-2026"                                        # version ID

# CLI defaults
smooth    = 3
smoothref = 1
mode      = 25
blorder   = 5
nsigma    = 5
ptype     = 'png'
frame     = 'icrs'
frame     = None

my_help = f"""
   This is the EDGE-HI pipeline, version {version}
   Currently supporting {projects[0]} (mode=0 or 15) and {projects[1]} (mode=1 or 25)
   Make sure $SDFITS_DATA has been set for mode=25 or full mode in mode=15
   Compressed 2015 data should be in data/AGBT15B_287_??.fits (39 files).

   Examples
      ./edge_hi.py --mode  4 U8503
      ./edge_hi.py --mode 15 NGC3815
      ./edge_hi.py --mode 25 UGC10972

   """

p = argparse.ArgumentParser(description=my_help, formatter_class=argparse.RawTextHelpFormatter)

p.add_argument('gal',                     nargs='?',           help=f'Galaxy, use all if left blank')
p.add_argument('--session', type = int,   default = None,      help=f'Force single session for given galaxy, [all]')
p.add_argument('--mode',    type = int,   default = mode,      help=f'0 or 15->2015 data   1 or 25->2025 data [{mode}]')
p.add_argument('--smooth',  type = int,   default = smooth,    help=f'boxcar smooth size (channels), use 0 to use raw. [{smooth}]')
p.add_argument('--smoothref',type = int,  default = smoothref, help=f'smooth reference size (channels), use 1 to skip. [{smoothref}]')
p.add_argument('--order',   type = int,   default = blorder,   help=f'baseline order fit (use -1 to skip) [{blorder}]')
p.add_argument('--nsigma',  type = float, default = nsigma,    help=f'nsigma [{nsigma}]')
p.add_argument('--v0',      type = float, default = None,      help=f'Override vlsr as center of galaxy [pars table entry]')
p.add_argument('--dv',      type = float, default = None,      help=f'Override dv for half signal portion  [pars table entry]')
p.add_argument('--dw',      type = float, default = None,      help=f'Override dw for each half baseline [pars table entry]')
p.add_argument('--table',   type = str,   default = None,      help=f'Optionally read in spectrum to overlay')
p.add_argument('--flags',   type = str,   default = None,      help=f'Flagging file with session,channel pairs')
p.add_argument('--frame',   type = str,   default = frame,     help=f'Velocity frame: itrs, gcrs, hcrs, icrs, lsrk, lsrd [{frame}]')
p.add_argument('--align',   action="store_false",              help='Do not align along choosen frame')
p.add_argument('--avechan',               default = None,      help=f'Number of channels to average in waterfall fits file [skip]')
p.add_argument('--plot',                  default = ptype,     help=f'Default plotting type [{ptype}]')
p.add_argument('--water',   action="store_true",               help='make waterfall plot')
p.add_argument('--full',    action="store_true",               help='Use full A/B/C data for mode=0')
p.add_argument('--batch',   action="store_true",               help='Batch mode, no interactive plots')
p.add_argument('--busy',    action="store_true",               help='add the busyfit (needs an extra install)')
p.add_argument('--nan',     action="store_false",              help='do not patch NaNs')
p.add_argument('--spike',   action="store_true",               help='attempt spike removal')
p.add_argument('--gps',     action="store_true",               help='attempt GPS flagging')
p.add_argument('--cog',     action="store_false",              help='use vel_cog instead of our vlsr')
p.add_argument('--show',    action="store_true",               help='only show galaxy session stats')
p.add_argument('--chan',    action="store_true",               help='show spectral axis in channels instead of km/s')
p.add_argument('--flux',    action="store_true",               help='Use Flux(Jy) instead of Ta(K)')
p.add_argument('--all',     action="store_true",               help='Run all galaxies (--batch recommended)')
p.add_argument('--test',    action="store_true",               help='Add some extra tests')
p.add_argument('--debug',   action="store_true",               help='Debug logging in dysh')



args = p.parse_args()

mode    = args.mode
smooth  = args.smooth
smoothref = args.smoothref
ss      = args.session
blorder = args.order
nsigma  = args.nsigma
vlsr    = args.v0
dv      = args.dv
dw      = args.dw
table   = args.table
flags   = args.flags
frame   = args.frame
avechan = args.avechan
ptype   = args.plot
my_gals = args.gal
Qwater  = args.water
Qfull   = args.full
Qbatch  = args.batch
Qbusy   = args.busy
Qnan    = args.nan
Qspike  = args.spike
Qgps    = args.gps
Qcog    = args.cog
Qshow   = args.show
Qchan   = args.chan
Qflux   = args.flux
Qalign  = args.align
Qall    = args.all
Qdebug  = args.debug
Qtest   = args.test

if Qdebug:
    print('ARGS',args)
    dysh.log.init_logging(1)

zenith_opacity = 0.008
if Qflux:
    print(f"Warning: working in Jy with assumed {zenith_opacity} zenith opacity")
    unit = "mJy"
else:
    print(f"Warning: working in K; co-adding spectra not perfect in flux and velocity")
    unit = "mK"
flux = dflux = flux6 = mad_rms = 0.0


if avechan is None:
    avechan = []
else:
    avechan = [int(num) for num in avechan.split(',')]    # can have 1 or 3 numbers

dysh_plots = []          # accumulate plots dysh makes, so we can quit them properly
rf_hi = 1420405751.786   # HI line restfreq in Hz

if Qdebug:
    print(args)

if Qbatch:
    print("MATPLOTLIB agg batch mode")
    import matplotlib
    matplotlib.use('agg')
else:
    print("MATPLOTLIB default interactive mode")
    import matplotlib.pyplot as plt    

def get_gals(filename = "gals15.pars", debug=True):
    """ reads galaxy parameters. Currently:
    gal       name
    session   1,2,...
    scans     comma separated list of the ON's
    vlsr      center of emission (km/s)              [optional after 1st pass]
    dv        half the width (km/s)                  [optional after 1st pass]
    dw        width of each baseline section (km/s)  [optional after 1st pass]
    """
    fp = open(filename)
    gals = {}
    for line in fp.readlines():
        if line[0] == '#': continue
        w = line.split()
        if len(w) < 3: continue        
        gal = w[0]
        if gal not in gals and len(w) < 6: continue
        session = int(w[1])
        scans = [int(x) for x in w[2].split(',')]
        if gal in gals:
            vlsr = dv = dw = None
        else:
            vlsr = float(w[3])
            dv = float(w[4])
            dw = float(w[5])
        if gal not in gals:
            gals[gal] = ([session],[scans],vlsr,dv,dw)
        else:
            gals[gal][0].append(session)
            gals[gal][1].append(scans)
    fp.close()
    if debug:
        print(f"Using {filename}")
        for k in gals.keys():
            print(k, gals[k])
        print(f"Found {len(gals)} objects")
    return gals

def set_flags(sdf, flags = None):
    """ for a given sdfits file, apply flags - a hack
    """
    print('SDF sessions',sdf.keys())
    if flags is None:
        return
    fp = open(flags)
    for line in fp.readlines():
        if line[0] == '#': continue
        w = line.split()
        #  w[0] session     w[1] scan    w[2] channel(s)
        session = int(w[0])
        scan    = int(w[1])
        # FLAGGING: 1 10 [5819, 5820, 8992, 8993, 9094, 9095, 9096, 9200, 8073]
        channel = [int(num) for num in w[2].split(',')]
        print("FLAGGING:",session,scan,channel)
        if session in sdf.keys():
            sdf[session].flag(scan=scan,channel=channel)
        else:
            print(f"Skipping flagging {session}, not in {sdf.keys()}")
    fp.close()
    

def get_pars(sdf, session, debug=True):
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
        if debug:
            print(gal,session,scans,vlsr,dv,dw)

def get_spectrum(file):
    """ read a spectrum from an ascii table
    Column 1:  v (km/s)
    Column 2:  intensity (units better match)
    no other columns!
    """
    print(f"Reading spectrum from {file}")
    (vel,sp) = np.loadtxt(file).T
    print('Vel :',vel[0],'...',vel[-1])
    print('Flux:',sp[0],'...',sp[-1],' Peak:',sp.max())
    return (vel,sp)

def patch_nan(sp):
    """   These are normally vegas spurs, could we just ignore them?
          Here we interpolate accross them. Disable with --nan
          Both the 2015 and 2025 data have NaN's in
          0-based channels [0,1,2,3]*8192, i.e. the first channel
          of the 4 "banks".
          
    """
    print("PATCH_NAN STATS",sp.stats())
    idx_nan = np.where(np.isnan(sp.flux))[0]
    nidx = len(idx_nan)
    print("IDX nan",idx_nan)
    for idx in idx_nan:
        if idx==0:
            sp._data[0] = sp._data[1]
        else:
            sp._data[idx] = 0.5*(sp._data[idx-1] + sp._data[idx+1])
        sp.mask[idx] = False
        print(f"Patching a NaN at {idx} to ", sp.data[idx])

def test_spikes(data, nrms=5):
    """  report spiky things
    """
    d = data[1:] - data[:-1]
    std = mad_std(d, ignore_nan=True)
    print("TEST_SPIKES:",std)
    clip = nrms * std
    idx = np.where(abs(d) > clip)
    print(idx)

# deprecated
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

# under development       
def patch_spike2(sp, n0, n1, clip):
    npatchp = 0
    npatchn = 0
    npatch1 = 0
    npatch2 = 0
    n = len(sp.data)
    d = sp.data
    print("Patch_spike2: nchan,n0,n1",n,n0,n1)
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
        for i in range(1,n-2):
            if last:
                last = False
                continue
            if abs(d[i]-d[i+1]) > clip:
                if abs(d[i-1]-d[i-2]) > clip: continue
                #if abs(d[i+2]-d[i+3]) > clip: continue
                if False:
                    sp.mask[i] = True
                    sp.mask[i+1] = True
                else:
                    sp.data[i]   = (2*sp.data[i-1] +   sp.data[i+2])/3
                    sp.data[i+1] = (  sp.data[i-1] + 2*sp.data[i+2])/3
                npatch2 = npatch2 + 1
                p.append(i)
                last = True
                print("spike2: ",i,d[i]-d[i+1])                
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
            
# under development       
def patch_spike3(sp, n0, n1, clip):
    """ based on NEMO's tabclip with clip== option
    """
    npt = len(sp.data)
    nf = 3
    ok = np.full(npt, True, dtype=bool)
    y = np.copy(sp.data)
    d = np.abs(y[1:]-y[:-1])
    d = np.roll(d,1)
    i = 1
    n1 = n2 = n3 = 0
    while i < npt - 1 - nf:
        if d[i]>clip and d[i+2]<clip:
            print(f"SPIKE1 at {i} {d[i]}  {d[i+1]} {d[i+2]}")
            ok[i] = False
            #sp.mask[i] = True
            sp.data[i] = 0.5*(y[i-1]+y[i+1])
            i = i + 2
            n1 = n1 + 1
            continue
        if d[i]>clip and d[i+1]>clip and d[i+3]<clip:
        #if d[i]>clip and d[i+1]>clip and y[i+2]+y[i+3]<2*clip:
            print(f"SPIKE2 at {i} {d[i]}  {d[i+1]} {d[i+2]} {d[i+3]}")
            #sp.mask[i] = True
            #sp.mask[i+1] = True
            ok[i] = False
            ok[i+1] = False
            sp.data[i] = 0.5*(y[i-1]+y[i+2])
            sp.data[i+1] = sp.data[i]
            n2 = n2 + 1            
            i = i + 3
            continue
        if d[i]>clip and d[i+1]>clip and d[i+2]>clip and d[i+4]<clip:
        #if d[i]>clip and d[i+1]>clip and d[i+2]>clip and y[i+3]+y[i+4]<2*clip:
            print(f"SPIKE3 at {i} {d[i]}  {d[i+1]} {d[i+2]} {d[i+3]} {d[i+4]}")
            #sp.mask[i] = True
            #sp.mask[i+1] = True
            #sp.mask[i+2] = True
            ok[i] = False
            ok[i+1] = False
            ok[i+2] = False
            sp.data[i] = 0.5*(y[i-3]+y[i+5])  ## 3
            sp.data[i+1] = sp.data[i]
            sp.data[i+2] = sp.data[i]
            n3 = n3 + 1
            i = i + 4
            continue
        i = i + 1
    print(f"With clip={clip} n1={n1} n2={n2} n3={n3}")


def busyfit(sp, gal, rms):
    """
    the busyfit
    """
    cmd = f"busyfit -c 1 2 {gal}.txt -n {rms} -o {gal} -noplot; sleep 2" 
    print("BUSYFIT:  ",cmd)
    os.system(cmd)

def edge2(sdf, gal, sessions, scans, vlsr, dv, dw, mode=1):
    """  pipeline for a galaxies; here sessions and scans are both lists
    
    mode=0 or 15    2015 ON-OFF-ON getsigref style  (final ON is sometimes missing)
    mode=1 or 25    2025 ON-OFF    getps style
    mode=2 or  4    2004 ON-OFF    getps without noise diode
    """
    global flux, dflux, flux6, mad_rms
    print(f"Working on {gal} {sessions} {scans} {vlsr} {dv} {dw}")

    ns1 = len(sessions)
    ns2 = len(scans)
    if ns1 != ns2:
        print("number of sessions and scans not the same")
        return None

    if Qflux:
        aflux = {"smoothref": smoothref, "zenith_opacity": zenith_opacity, "units": "flux"}
    else:
        aflux = {"smoothref": smoothref}

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
                if True:
                    sdf1.write('junk.fits',scan=scans_tp,fdnum=0,plnum=0,ifnum=0, overwrite=True)
                    sdf2 = GBTFITSLoad('junk.fits')
                    specs2 = sdf2.rawspectra(0,0)
                    std2 = np.std(specs2, axis=1).data
                    np.savetxt(f'{gal}_water_{sessions[i]}.tab', std2)
                sb1 = sdf1.gettp(scan=scans_tp,fdnum=0,plnum=0,ifnum=0)
                sss = sb1.plot(vmax=1e10)
                dysh_plots.append(sss)
                print(sss)
                sss.savefig(f'{gal}_water_{sessions[i]}.png')
                if len(avechan) > 0:
                    if len(avechan) > 1:
                        sss.write(f'{gal}_water_{sessions[i]}.fits', avechan[0], avechan[1:], overwrite=True)
                    else:
                        sss.write(f'{gal}_water_{sessions[i]}.fits', avechan[0], overwrite=True)
                #plt.show()
            print(f"Session {sessions[i]}  Scan {scans[i]}")
            if True:
                if Qtest:
                    # test for spikes
                    tp0 = sdf[sessions[i]].gettp(scan=scans[i], fdnum=0, ifnum=0, plnum=0).timeaverage()
                    test_spikes(tp0.flux.value)
                # combine all scans
                sp0 = sdf[sessions[i]].getps(scan=scans[i], fdnum=0, ifnum=0, plnum=0, **aflux).timeaverage()
                sp1 = sdf[sessions[i]].getps(scan=scans[i], fdnum=0, ifnum=0, plnum=1, **aflux).timeaverage()
                sp.append(sp0)
                sp.append(sp1)
            else:
                # each scan separate; may be needed if very high spectral resolution is used
                for s in scans[i]:
                    sp0 = sdf[sessions[i]].getps(scan=s, fdnum=0, ifnum=0, plnum=0, **aflux).timeaverage()
                    sp1 = sdf[sessions[i]].getps(scan=s, fdnum=0, ifnum=0, plnum=1, **aflux).timeaverage()
                    sp.append(sp0)
                    sp.append(sp1)
            
    if mode == 2:    # 2004 data
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
                dysh_plots.append(sss)
                print(sss)
                sss.savefig(f'{gal}_water_{sessions[i]}.png')
                if len(avechan) > 0:
                    if len(avechan) > 1:
                        sss.write(f'{gal}_water_{sessions[i]}.fits', avechan[0], avechan[1:], overwrite=True)
                    else:
                        sss.write(f'{gal}_water_{sessions[i]}.fits', avechan[0], overwrite=True)
                #plt.show()
            sp0 = sdf[sessions[i]].getps(scan=scans[i], fdnum=0, ifnum=0, plnum=0, t_sys=25.84, **aflux).timeaverage()
            sp1 = sdf[sessions[i]].getps(scan=scans[i], fdnum=0, ifnum=0, plnum=1, t_sys=30.49, **aflux).timeaverage()

            if True:
                sp.append(sp0.average(sp1))
            else:
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
                if True:
                    sdf1.write('junk.fits',scan=scans_tp,fdnum=0,plnum=0,ifnum=1, overwrite=True)
                    sdf2 = GBTFITSLoad('junk.fits')
                    f = sdf2.getspec(0).frequency.value   # topocentric
                    print("PJT",f.min(),f.max())
                    idx1 = np.abs(f-1.380).argmin()
                    idx2 = np.abs(f-1.382).argmin()
                    if idx1 > idx2:
                        idx1,idx2 = idx2,idx1
                    print("PJT",idx1,idx2)
                    specs2 = sdf2.rawspectra(0,0)[:,idx1:idx2]
                    std2 = np.std(specs2, axis=1).data
                    np.savetxt(f'{gal}_water_{sessions[i]}.tab', std2)
                sb1 = sdf1.gettp(scan=scans_tp,fdnum=0,plnum=0,ifnum=1)
                sss = sb1.plot(vmax=1e10)
                dysh_plots.append(sss)
                sss.savefig(f'{gal}_water_{sessions[i]}.png')
                if len(avechan) > 0:
                    if len(avechan) > 1:
                        sss.write(f'{gal}_water_{sessions[i]}.fits', avechan[0], avechan[1:])
                    else:
                        sss.write(f'{gal}_water_{sessions[i]}.fits', avechan[0])
                #plt.show()
            for s in scans[i]:
                for pl in [0,1]:
                    #  we will try/except since sessions are not a multiple of 3 scans
                    #  but we need s, s+1 and s+2
                    if Qtest:
                        # test spikes
                        tp1 = sdf1.gettp(scan=s, fdnum=0, ifnum=1, plnum=pl).timeaverage()
                        test_spikes(tp1.flux.value)
                    
                    try:
                        sp1 = sdf1.getsigref(scan=s,ref=s+1,fdnum=0,ifnum=1,plnum=pl, **aflux).timeaverage()
                        sp.append(sp1)
                    except:
                        print(f"Skipping missing scan {s+2} pol {pl}")
                    try:
                        sp2 = sdf1.getsigref(scan=s+2,ref=s+1,fdnum=0,ifnum=1,plnum=pl, **aflux).timeaverage()
                        sp.append(sp2)
                    except:
                        print(f"Skipping missing scan {s+2} pol {pl}")

    if Qalign:
        # align spectra: it is important align_to() comes before set_frame()
        # also print velocity axis in middle of spectrum
        for i,sp_i in enumerate(sp):
            sp_kms = sp_i.with_spectral_axis_unit("km/s").spectral_axis[sp_i.nchan//2].value
            print(f"KM/S[0 ] {i} = {sp_kms}  {sp_i.nchan}  {id(sp_i)}  {id(sp[i])}")
            if i == 0:
                if frame is not None:
                    sp_i.set_frame(frame)
            else:
                sp[i] = sp_i.align_to(sp[0], method="interpolate")   # issue : fft method can cause spikes at 16384
                if frame is not None:
                    sp[i].set_frame(frame)
            sp_kms = sp[i].with_spectral_axis_unit("km/s").spectral_axis[sp_i.nchan//2].value
            print(f"KM/S[1a] {i} = {sp_kms}  {sp_i.nchan}  {id(sp_i)}  {id(sp[i])}")
    for i,sp_i in enumerate(sp):
        if frame is not None:
            sp[i].set_frame(frame)   # set (again), in case no align was done
        sp_kms = sp_i.with_spectral_axis_unit("km/s").spectral_axis[sp_i.nchan//2].value
        print(f"KM/S[2 ] {i} = {sp_kms}  {sp_i.nchan} {id(sp_i)}  {id(sp[i])} {sp_i.velocity_frame}")

                
    if len(sp) == 0:
        print("Did not find any scans")
        return None

    if Qgps:
        print("GPS flagging not implemented yet")

    vmin = vlsr-dv-dw
    vmax = vlsr+dv+dw
    gmin = vlsr-dv
    gmax = vlsr+dv
    gmin6 = vlsr-600
    gmax6 = vlsr+600

    sp = sp[0].average(sp[1:])    # average all scans
    if Qnan:
        patch_nan(sp)

    sp.set_convention("optical")   # 2015 data was in radio convention, 2025 was ok

    #  if you haven't ensured the restfreq is correct, do it here
    sp.rest_value = rf_hi * u.Hz

    print(f"Looking at {vlsr} from {vmin} to {vmax}")
    spn = sp[vmin*kms:vmax*kms]

    if Qspike:
        spb0 = spn[vmin*kms:gmin*kms]
        spb1 = spn[gmax*kms:vmax*kms]
        rms = min(spb0.stats(roll=2)["rms"], spb1.stats(roll=2)["rms"])   # @todo try mad_rms
        n0 = len(spb0.data)
        n1 = len(spb1.data)
        #patch_spike2(spn, n0, n1, 5*rms.value)
        patch_spike3(spn, n0, n1, nsigma*rms.value)

    if smooth > 0:
        # issue 1067:  smoothing changes the input spectrum
        sps = spn.smooth("box",smooth, nan_treatment='interpolate', preserve_nan = False)
        if frame is not None:
            sps.set_frame(frame)  # see issue 1057   "smooth() returns a spectrum in itrs frame"
        if blorder >= 0:
            sps.baseline(blorder,exclude=(gmin*kms,gmax*kms),remove=True)
            print("Baseline model 1 excl:",sps.baseline_model)
    else:
        sps = spn
        if frame is not None:
            sps.set_frame(frame)   # make sure it's set, in case --align was used
        if blorder >= 0:
            sps.baseline(blorder,include=[(vmin*kms,gmin*kms),(gmax*kms,vmax*kms)],remove=True)            
            print("Baseline model 2 incl:",sps.baseline_model)

    #   @todo :  try another patch_spike3?

    #   flux : simple sum between gmin and gmax
    spg = sps[gmin*kms:gmax*kms]
    ngal = len(spg.flux)
    sumflux = np.nansum(spg.flux)
    deltav = abs(spg.velocity[0]-spg.velocity[1])
    flux = sumflux * deltav
    vlsr2 = np.nansum(spg.flux * spg.velocity) / sumflux              # @todo  these are wrong 2x
    vlsr3 = np.nansum(sps.flux * sps.velocity) / np.nansum(sps.flux)  # @todo  these are wrong 2x
    print(f"VEL: v0={vlsr}  vlsr2={vlsr2}  vlsr3={vlsr3}")

    spg6 = sps[gmin6*kms:gmax6*kms]
    flux6 = np.nansum(spg6.flux) * deltav
    print(f"FLUX6 = {flux6}")

    spb0 = sps[vmin*kms:gmin*kms]
    spb1 = sps[gmax*kms:vmax*kms]

    rms0_0 = (spb0.stats()['rms']).to(unit)
    rms1_0 = (spb1.stats()['rms']).to(unit)
                    
    rms0_1 = (spb0.stats(roll=1)['rms']).to(unit)
    rms1_1 = (spb1.stats(roll=1)['rms']).to(unit)

    rms0_2 = mad_std(spb0.flux.to(unit), ignore_nan=True)
    rms1_2 = mad_std(spb1.flux.to(unit), ignore_nan=True)
    mad_rms = max(rms0_2,rms1_2)

    ad1 = spb0.normalness()  # baseline left
    ad2 = spb1.normalness()  # baseline right
    ad3 = spg.normalness()   # galaxy (possibly smoothed)
    ad0 = spn.normalness()   # whole interval

    print(f'RMS:    roll=0    roll=1     mad_std')
    print(f'rms0: {rms0_0:.1f} {rms0_1:.1f} {rms0_2:.1f} left')
    print(f'rms1: {rms1_0:.1f} {rms1_1:.1f} {rms1_2:.1f} right')

    # has no meaning if flux was used
    rad1 = spb0.radiometer()
    rad2 = spb1.radiometer()
    print(f'radiometer: {rad1} {rad2}')

    rms = max(rms0_1,rms1_1)
    Qb = max(rms0_0, rms0_1, rms1_0, rms1_1) / min(rms0_0, rms0_1, rms1_0, rms1_1)

    print(f'Anderson-Darling normalness test: {ad1:.2f}  {ad2:.2f} {ad3:.2} {ad0:.3}      Qb {Qb:.2f}')

    if Qflux: 
        dflux = mad_rms.to("Jy")*deltav*np.sqrt(ngal)
    else:
        dflux = mad_rms.to("K")*deltav*np.sqrt(ngal)

    pars = {}
    pars['Qb'] = Qb
    pars['flux'] = flux
    pars['dflux'] = dflux
    pars['rms'] = mad_rms    # better than rms, since it's subject to spikes
    pars['vlsr2'] = vlsr2
    
    # https://dysh.readthedocs.io/en/latest/explanations/cog/index.html
    # https://dysh.readthedocs.io/en/latest/users_guide/cog.html
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
        if Qflux:
            busyfit(sps, gal, rms.value)
        else:
            busyfit(sps, gal, rms.to("K").value)

    print(f"{gal:.15s} Flux: {flux.value:.2f} +/- {dflux:.2f}  {flux2:.2f}  w95 {w95:.1f} rms {rms:.2f} Qb {Qb:.2f} Qa {Qa:.2f} nchan {ngal}")

    return sp, sps, pars
    # end_of_edge2

def spectrum_plot(sp, gal, project, vlsr, dv, dw, pars, label="smooth", spbl = None, Qchan = False, table=None):
    """   a more dedicated EDGE plotter, hardcoded units in km/s and mK
          uses matplotlib

          spbl:   optional sp with baseline solution to plot
          Qchan:  simpler plot with just channel numbers
          table:  optional spectrum to overlay
    """
    import matplotlib.pyplot as plt    # not needed here anymore

    print("SPECTRUM_PLOT =============================================")

    drawstyle = { 'drawstyle': 'steps-mid'}

    vel = sp.axis_velocity().value
    #vel = sp.with_velocity_convention('optical').axis_velocity().value
    print("Velocity axis:",vel[0],vel[-1])
    ch  = np.arange(len(vel))
    sflux = sp.flux.to(unit).value
    #fig=plt.figure(figsize=(8,4))
    fig,ax1 = plt.subplots()
    Qb = pars["Qb"]
    w95 = pars["w95"]
    if Qchan:
        plt.plot(ch, sflux,label=f'w95 {w95:.1f}',**drawstyle)
        return
    else:
        plt.plot(vel,sflux,label=f'w95 {w95:.1f}',**drawstyle)
    if sp.subtracted:
        print(f"Showing baseline fit with {len(vel)} channels")
        if spbl is not None:
            # need to find the slice on sp.spectral_axis
            # sp.spectral_axis.to(kms)[0] to [-1]
            bl = spbl._baseline_model(sp.spectral_axis).to(unit)
            plt.plot(vel,bl,color='red',label='subtracted')
        else:
            print("PJT: sp - no offset plot of baseline done")
            bl = sp._baseline_model(sp.spectral_axis).to(unit)
            # don't plot, it's offset
        bl._vel = vel
    else:
        print(f"No native baseline fit with {len(vel)} channels")
        bl = None
    if spbl is not None:
        print("BL fit:")
        #print(f"BL:",spbl[0],spbl[-1])
        #print(f"VEL:  {spbl._vel[0]} .. {spbl._vel[-1]}")
        plt.plot(spbl._vel,spbl,color='red',label=f"baseline_{blorder}")
    print("PARS:",pars)
    rms = pars["rms"].to(unit).value
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
            ax1.plot(xb,yb, color='black', label=f'rms={rms:.1f} {unit} Qb={Qb:.2f}')
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
    # optional table overlay
    if table is not None:
        print("TABLE",table)
        (tvel, tint) = get_spectrum(table)
        ax1.plot(tvel,tint,color='red',linestyle='dashed',label=table)
    # draw a vlsr line in green
    ax1.plot([vlsr,vlsr],[-rms,+rms],color='green',label=f'v0={vlsr} km/s')
    # draw the cog() 'vel' in red, as long as it's not 0
    vel_cog = pars['vel_cog']
    if vel_cog != 0.0:
        ax1.plot([vel_cog,vel_cog],[rms,3*rms],color='red',label=f'vel_cog={vel_cog:.1f} km/s')    
    #
    plt.text
    plt.xlabel(f"Velocity {sp.velocity_frame} (km/s)")     # grab the frame it has
    plt.ylabel(f"Intensity ({unit})")
    plt.title(f'{gal} {project}  Flux: {flux.value:.2f} +/- {dflux:.2f}')
    plt.legend()
    plt.savefig(f"{gal}_{label}.png")
    #plt.show()
    return bl
    # <end> spectrum_plot
    
# deprecate
def g_test(sp, size=10):
    """kanekar test
    Based on mock gaussian spectra, 95% of the gaussian spectra have 1.16 >= g_test >= 0.79. 
    So, a threshold of 0.79 and 1.16 could be a good value for rejecting non gaussian spectra 
    (i.e., a spectrum is non gaussian if 0.79 < g_test < 1.16).
    """
    ratio = sp.smooth("box", size).stats()["rms"] * np.sqrt(size) / sp.stats()["rms"]
    return ratio


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
    elif mode==2 or mode==4:
        gals = get_gals("gals04.pars")
        mode=2

    # alternatively, mode points to the pars file already
    if False and os.path.exists(mode):
        gals = get_gals(mode)
        mode = 3 

    if Qshow:
        print(f"Found {len(gals)} galaxies in {projects[mode]}")
        sys.exit(0)

    if my_gals is None:
        if not Qall:
            print("Need --all to run pipeline for all galaxies")
            sys.exit(0)
        my_gals = gals.keys()
    else:
        # only one galaxy
        my_gals = [my_gals]

    project = projects[mode]

    sdf = {}
    if mode == 0:
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
                #sdf[session] = GBTFITSLoad(filename, skipflags=False)     # flag_vegas=False, skipflags=True)
                #sdf[session] = GBTFITSLoad(filename)
                sdf[session] = GBTOffline(filename)
            sdf[session]["RESTFREQ"] = rf_hi             # should really use sp.rest_value = 1.4... * u.Hz
            sdf[session].summary()
            print('FLAGS',sdf[session].final_flags)
        set_flags(sdf, flags)

    elif mode == 1:
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
            sdf[session] =  GBTOffline(filename)  # flag_vegas=False, skipflags=True)
            sdf[session].summary()
            print('FLAGS',sdf[session].final_flags)

    elif mode == 2:
        print("2016 hi_survey data", my_gals)
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
                filename = f'AGBT04A_008_{session:02}'
                print("Opening",filename)
                sdf[session] = GBTOffline(filename)
            else:
                #filename = f'{project}/{project}_{session:02}.B.fits'
                #filename = f'data/{project}_{session:02}.B.fits'
                filename = f'{project}_{session:02}.raw.acs.fits'
                print(f"# === {filename}")
                sdf[session] = GBTOffline(filename)     # flag_vegas=False, skipflags=True)
            sdf[session]["RESTFREQ"] = rf_hi             # should really use sp.rest_value = 1.4... * u.Hz
            sdf[session].summary()
            print('FLAGS',sdf[session].final_flags)

    elif mode == 99:
        # work in progress
        print("getPS style", my_gals)
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
                filename = f'AGBT04A_008_{session:02}'
                print("Opening",filename)
                sdf[session] = GBTOffline(filename)
            else:
                #filename = f'{project}/{project}_{session:02}.B.fits'
                #filename = f'data/{project}_{session:02}.B.fits'
                filename = f'{project}_{session:02}.raw.acs.fits'
                print(f"# === {filename}")
                sdf[session] = GBTOffline(filename)     # flag_vegas=False, skipflags=True)
            sdf[session]["RESTFREQ"] = rf_hi             # should really use sp.rest_value = 1.4... * u.Hz
            sdf[session].summary()
            print('FLAGS',sdf[session].final_flags)
            
    ngal = len(my_gals)
    for (gal,i) in zip(my_gals,range(ngal)):
        print("\n=====================================")
        print(f"{gal}  {i+1}/{ngal}")
        sessions, scans, vlsr1, dv1, dw1 = gals[gal]
        if Qall:
             vlsr = vlsr1
             dv = dv1
             dw = dw1
        else:
            if vlsr is None:  vlsr = vlsr1
            if dv   is None:  dv   = dv1
            if dw   is None:  dw   = dw1
        print("SESSIONS:",sessions)
        if ss is not None and not ss in sessions:
            continue
        # edge2() will do optional waterfall
        sp,sps,pars = edge2(sdf, gal, sessions, scans, vlsr, dv, dw, mode)
        #sss = sps.plot(xaxis_unit="km/s", doppler_convention='optical')  # vel_frame=
        sss = sps.plot(xaxis_unit="km/s")  # doppler_convention='optical')  # vel_frame=
        dysh_plots.append(sss)
        sss.savefig(f'{gal}_dysh.png')
        #plt.show()
        # convert spectrum to one with velocities
        sps1 = sps.with_spectral_axis_unit("km/s")
        sps1.write(f'{gal}.txt',format="ascii.commented_header",overwrite=True)
        # zoomed version
        bl = spectrum_plot(sps, gal, project, vlsr, dv, dw, pars, "smooth", spbl = None, table=table)
        # full spectrum
        spectrum_plot(sp,  gal, project, vlsr, dv, dw, pars, "wide", spbl = bl, Qchan=Qchan)
        if not Qbatch:
            plt.show()
        print("SPS QAC checksum:",sps.stats(qac=True))
        print("Channel spacing:",sps.velocity[1]-sps.velocity[0])
        print("-----------------------------------")

        # stuff for the EDGE_PYDB output csv
        Name = gal
        Refcode = refcodes[mode]
        Vsys = vlsr
        Deltav = (sps.velocity[1]-sps.velocity[0]).value
        Robust_rms = mad_rms.value
        RefInt = flux6.value
        RefUnc = dflux.value
        SigInt = flux.value
        SigUnc = dflux.value
        SigVmin = vlsr - dv
        SigVmax = vlsr + dv
        BadFlag = False
        print("Name,Refcode,Vsys,Deltav,Robust_rms,RefInt,RefUnc,SigInt,SigUnc,SigVmin,SigVmax,BadFlag")
        msg = f"{Name},{Refcode},{Vsys},{Deltav:.2f},{Robust_rms:.2f},{RefInt:.2f},{RefUnc:.2f},{SigInt:.2f},{SigUnc:.2f},{SigVmin},{SigVmax},{BadFlag}"
        cmd = " ".join(sys.argv[1:])
        print(f"{msg} {cmd} EDGE_PYDB")
        with open("edge_hi.log","a") as f:
            f.write(f"{msg}  {cmd}\n")


    if not Qbatch:
        if len(dysh_plots) > 0:
            print(f"dysh plotting blocking needed for {len(dysh_plots)} plot(s)")
            dysh_plots[0].show(block=True)
        ans = input(f"Hit enter to exit script")
