# operator-run script for AGBT25A_474
# Y.-H. Eltha Teng, Oct 2025

########## SETTINGS #############
h = Horizon(20.0)  # minimum of 20 degrees elevation
myOff = Offset("AzEl", 1.0, 0.0, cosv=True)  # Off position relative to source
doFirstPointing = True  # Setting to False will skip the first pointing
doFirstCal = True  # Setting to False will skip the first 3C calibrator OnOff scan
scanTime = 180  # 180 seconds = 3 min for an on OR off scan 
n_scans = 5  # do OnOff for 5 time on each science source (i.e. 15 min on + 15 min off per source)
n_repeat = 1  # observe once per source
keyhole = 74  # maximum elevation limit of GBT (in degree)
#####################################

ResetConfig()

config_string = """
receiver = 'Rcvr1_2'
obstype = 'Spectroscopy'
backend = 'VEGAS'
restfreq = 1420.4058
bandwidth = 187.5
nchan = 32768
swmode = "tp"
swtype = "none"
swper = 1.0
tint = 5.0
vframe = "bary"
vdef = "Optical"
noisecal = "lo"
pol = "Linear"
"""

Configure(config_string)

execfile("/users/yteng/EDGE-HI/25A474_functions.py")
Catalog(fluxcal)
Catalog(lband_pointing)

tdelta = DateTime.TimeDelta(minutes=5)  
obs_count = 0
doCal = doFirstCal
doPointing = doFirstPointing
project_obs = 0
old_catalog_name = 'dummy'
fullcat = '/users/yteng/EDGE-HI/targets.cat'


while project_obs < 100:
    
    mycat, altcal = select_my_catalog()
    obs_per_source = n_repeat * n_scans
    
    if mycat == old_catalog_name:
        print 'SAME CATALOG HAS BEEN SELECTED: Using FULL catalog'
        mycat = fullcat
        altcal = '3C309_1'    
    old_catalog_name = mycat

    c = Catalog(mycat)
    sources = c.keys()

    for source in sources:
        
        doBalance = True
        
        ## Pick an observable science source along with its nearby calibrator
        calibrator = c[source]["calibrator"]
        n_obs = int(float(c[source]["n_obs"]))
        obs_left = obs_per_source - n_obs
        obs_ok = obs_left > 0

        t_now = Now()
        alt_ok = True  # source altitute should be ok in most cases 
        if t_now != None and obs_ok:
            source_rise = h.GetRise(source)
            source_set  = h.GetSet(source)
            if source_rise != None:
                if source_set != None:
                    t_ok = ((t_now + tdelta) < source_set)
                    t_ok = t_ok and (t_now >= source_rise)
                else:
                    t_ok = True
            else:
                t_ok = False
            
            if t_ok:
                ## Skip source if it is near zenith
                source_ra = c[source]["ra"]  # float in deg
                source_dec = c[source]["dec"]  # float in deg
                source_alt = get_altitude(source_ra, source_dec, t_now)
                alt_ok = False if source_alt > keyhole else True
        else:
            t_ok = False

        source_ok = t_ok and obs_ok and alt_ok

        ## Source confirmed; calibrate (if first source) and do science scans
        if source_ok:
            if doPointing == True:
                ## check the calibrator is above the horizon
                if h.GetRise(calibrator) > t_now:
                    myCal = altcal ##circumpolar alternative
                    print 'Calibrator %s is too low: Using %s' %(calibrator,altcal)
                else:
                    myCal = calibrator
                if obs_count == 0:
                    AutoPeakFocus(myCal)
                    #Break("Check Peak and Focus")
                else:
                    AutoPeak(myCal)

                ResetConfig()
                Configure(config_string)
                doBalance = True
                doPointing = False

            if doCal:
                Slew(myCal)
                Balance()
                print 'Calibration scans (OnOff) :%s ' %(myCal)
                OnOff(myCal, myOff, scanTime)
                doCal = False
                doBalance = True

            ## Starting science scans
            for i in range(obs_left):
                ## Checking time ok again
                t_now = Now()   
                t_ok = False
                if t_now != None:
                    if source_rise != None:
                        if source_set != None:
                            t_ok = ((t_now + tdelta) < source_set)
                            t_ok = t_ok and (t_now >= source_rise)
                        else:
                            t_ok = True
                    else:
                        t_ok = False
                else:
                    t_ok = False

                ## Starting science OnOff scans
                if t_ok:
                    ## Re-balance when source changes
                    if doBalance:
                        Slew(source)
                        Balance()
                        doBalance = False

                    Comment("Starting on-off scan")
                    OnOff(source, myOff, scanTime)

                    obs_count = obs_count + 1
                    obs_tot = obs_per_source + 1 - obs_left + i
                    print '%s: OBS COMPLETE = %s/%s' %(source, obs_tot, obs_per_source)
                    
                    update_my_catalogs(source, obs_tot)

        if source_ok and mycat == fullcat:
            break
    
    project_obs = project_obs + 1
