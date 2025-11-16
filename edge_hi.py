#! /usr/bin/env dysh
#
# typical scan has 37 x 2.5sec exposures = 92.5 sec  (both the ON and OFF)

gals = {
    #   name     session   scans            vlsr   dv    dw
    "UGC10972" :  ( "01",  [8,10,12,14,16],  4650,  250, 1000),
    "NGC6154"  :  ( "01",  [18,20,22],       5980,  100,  400),
    "NGC5480"  :  ( "01",  [25,27,29,31,33], 1870,  200,  800),
    "NGC5633"  :  ( "01",  [35,37,39,41,43], 2300,  200,  800),    
    "UGC09476" :  ( "01",  [45,47,51,53],    3230,  150,  600),    # 49 bad
    "UGC08733" :  ( "01",  [55,57,59],       2315,  150,  600),    # 61 last "ON", has no "OFF"
}


# at GBO:     sdf = GBTOnline()
#             sdf = GBTOffline('AGBT25A_474_01')
#  rsync -av  /home/sdfits/AGBT25A_474_01   teuben@lma.astro.umd.edu:/lma1/teuben/GBT
#
# d76:
#  rc dysh5
#  export SDFITS_DATA=/home/teuben/EDGE/GBT-EDGE-HI
#  rsync -av lma:/lma1/teuben/GBT/AGBT25A_474_01 .
#  

import astropy.units as u
kms = u.km/u.s

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

    if False:
        sps = spn.smooth("box",0)
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
                    
    dflux = rms.to("K")*deltav*np.sqrt(ngal)
    print(f"{gal:.10s} Flux: {flux:.2f} +/- {dflux:.2f}   rms {rms:.2f}    nchan {ngal}")


    print('sps.plot(xaxis_unit="km/s")')

    return sp, sps


sdf = GBTOffline('AGBT25A_474_01')
sdf.summary()

for gal in gals.keys():
    print(gal)
    session, scans, vlsr, dv, dw = gals[gal]
    sp,sps = edge1(sdf, gal, session, scans, vlsr, dv, dw)
    sss = sps.plot(xaxis_unit="km/s")
    sss.savefig(f'{gal}.png')
    print("-----------------------------------")
