#! /usr/bin/env python
#               dysh      (issue 946)
#
# Import an ascii table into dysh, and compute flux using COoG method
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
import pprint

from dysh.spectra.spectrum import Spectrum
from dysh.coordinates import Observatory

from IPython import embed

version     = "3-jun-2026"                                        # version ID

#%%

# CLI defaults
xcol      = 1
ycol      = 2
smooth    = 3
smoothref = 1
blorder   = 5
nsigma    = 5
ptype     = 'png'
frame     = 'icrs'
frame     = None

my_help = f"""
   Import an ascii table into dysh and compute flux using CoG.

   Currently only working for HI.

   Warning, the CLI is still largely that of edge_hi.py and has
   no meaning here. Some of these are meant to be implemented for
   these arbitrary tabular spectra.

   """

p = argparse.ArgumentParser(description=my_help, formatter_class=argparse.RawTextHelpFormatter)

p.add_argument('tab',                     nargs='?',           help=f'Table')

p.add_argument('--xcol',    type = int,   default = xcol,      help=f'Column to represent spectral axis. [{xcol}]')
p.add_argument('--ycol',    type = int,   default = ycol,      help=f'Column to represent flux. [{ycol}]')

p.add_argument('--smooth',  type = int,   default = smooth,    help=f'=boxcar smooth size (channels), use 0 to use raw. [{smooth}]')
p.add_argument('--order',   type = int,   default = blorder,   help=f'=baseline order fit (use -1 to skip) [{blorder}]')
p.add_argument('--nsigma',  type = float, default = nsigma,    help=f'=nsigma [{nsigma}]')
p.add_argument('--v0',      type = float, default = None,      help=f'=Override vlsr as center of galaxy [pars table entry]')
p.add_argument('--dv',      type = float, default = None,      help=f'=Override dv for half signal portion  [pars table entry]')
p.add_argument('--dw',      type = float, default = None,      help=f'=Override dw for each half baseline [pars table entry]')
p.add_argument('--table',   type = str,   default = None,      help=f'=Optionally read in spectrum to overlay')

p.add_argument('--frame',   type = str,   default = frame,     help=f'=Velocity frame: itrs, gcrs, hcrs, icrs, lsrk, lsrd [{frame}]')
p.add_argument('--align',   action="store_false",              help=f'=Do not align along choosen frame')
p.add_argument('--avechan',               default = None,      help=f'=Number of channels to average in waterfall fits file [skip]')
p.add_argument('--plot',                  default = ptype,     help=f'=Default plotting type [{ptype}]')

p.add_argument('--batch',   action="store_true",               help='=Batch mode, no interactive plots')
p.add_argument('--busy',    action="store_true",               help='=add the busyfit (needs an extra install)')
p.add_argument('--nan',     action="store_false",              help='=do not patch NaNs')
p.add_argument('--spike',   action="store_true",               help='=attempt spike removal')

p.add_argument('--cog',     action="store_false",              help='=use vel_cog instead of our vlsr')
p.add_argument('--show',    action="store_true",               help='=only show galaxy session stats')
p.add_argument('--chan',    action="store_true",               help='=show spectral axis in channels instead of km/s')
p.add_argument('--flux',    action="store_true",               help='Use Flux(Jy) instead of Ta(K) as assumed from input table')
p.add_argument('--all',     action="store_true",               help='=Run all galaxies (--batch recommended)')
p.add_argument('--debug',   action="store_true",               help='Debug logging in dysh')



args = p.parse_args()

smooth  = args.smooth
blorder = args.order
nsigma  = args.nsigma
vlsr    = args.v0
dv      = args.dv
dw      = args.dw
table   = args.table
frame   = args.frame
avechan = args.avechan
ptype   = args.plot
my_tab  = args.tab
Qbatch  = args.batch
Qbusy   = args.busy
Qnan    = args.nan
Qspike  = args.spike
Qcog    = args.cog
Qshow   = args.show
Qchan   = args.chan
Qflux   = args.flux
Qalign  = args.align
Qall    = args.all
Qdebug  = args.debug

if Qdebug:
    print('ARGS',args)
    dysh.log.init_logging(1)

if Qflux:
    print(f"Warning: assumed working in Jy")
    unit = "mJy"
else:
    print(f"Warning: assumed working in K")
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

#%%

def get_spectrum(file, xcol=1, ycol=2):
    """ read a spectrum from an ascii table;
    Column 1:  v (km/s)
    Column 2:  intensity (units better match)
    """
    print(f"Reading spectrum from {file}")
    # skip potentially bad columns, only read the specified ones'
    data = np.loadtxt(file, usecols=(xcol-1,ycol-1)).T
    vel = data[0]
    sp = data[1]
    print('Vel :',vel[0],'...',vel[-1], ' km/s (assumed)')
    print('Flux:',sp[0],'...',sp[-1],' Peak:',sp.max())
    return data


#%%

if __name__ == "__main__":

    if my_tab == None:
        my_tab = "test.tab"

    data = get_spectrum(my_tab, xcol, ycol)
    nchan = len(data[0])
    print("NCHAN:",nchan)

    sp1 = Spectrum.fake_spectrum(nchan)
    
#%%
    
    sa = (data[xcol-1] + 1000) * u.km/u.s
    if Qflux:
        flux = data[ycol-1] * u.Jy 
    else:
        flux = data[ycol-1] * u.K  
    if vlsr is None:
        vlsr = 0.0       # value doesn't matter for cog()
    print("VLSR:",vlsr)
    # borrow from fake_spectrum
    meta = sp1.meta
    crval1 = nchan//2     # because of non-linear, flux depends on crval1 (1%)
    meta['CRVAL1'] = data[xcol-1][crval1]
    meta['CRPIX1'] = 1.0
    meta['CDELT1'] = data[xcol-1][crval1] - data[xcol-1][crval1-1]
    meta['CTYPE1'] = 'VELO-HEL'
    meta['CUNIT1'] = 'km/s'
    meta['VELOCITY'] = vlsr * 1000.0
    
    sp4 = Spectrum.make_spectrum(data = flux,
                                 meta = meta,
                                 use_wcs = True,
                                 observer_location = Observatory["GBT"])
    print(sp4)
    cog = sp4.cog()
    pprint.pprint(cog, width=1)
