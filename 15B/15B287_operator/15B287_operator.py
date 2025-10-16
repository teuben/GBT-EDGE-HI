# test script to update catalog as you go...

########## CHANGE THESE ONLY #############
OnOffOnTime = 21 #minutes (change this to 12 to be in line with DSS scheduling)
obs_per_source = 3 #total observing time per source = OnOffOnTime * obs_per_source
h = Horizon(10.0) #minimum of 10 degrees elevation
myOff = Offset("J2000",1.0,0.0,cosv=True)  # Off position relative to source
doFirstPointing = True #Setting to False will skip the first pointing
doFirstCal = True  #Setting to False will skip the first 3C calibrator OnOff scan
peak_every = 6 #peak/cal every 6 OnOffOn (every 2.5 hours) 12 if changed
peak_near_source = False #Do another peak when changing to new source
#####################################

######### NOTES ###############
# This script runs in blocks of On-Off-On position switching with
# the two outer 'on' scans sharing one 'off'
# Total on-source time = 42 minutes   (24 if changes)
# Length of one 'On' or 'Off' = 7 minutes   (4 minutes if changes)
# Length of one On-Off-On = 21 minutes (14 minutes on-source)    (12 min if changes)
# 3 On-Off-On blocks are needed per source (63 minutes altogether)  (36 minutes if changes)
# !!!! Please remember to update catalog after session is complete

###### Timing
# It takes 1h 8m to completely observe 1 source+overhead (9 track scans)

execfile("/home/astro-util/projects/15B287_operator/15B287_config.py")
execfile("/home/astro-util/projects/15B287_operator/15B287_utils.py")
Catalog(fluxcal)
Catalog(lband_pointing)

scanTime = OnOffOnTime * 20.0 #seconds
tdelta = DateTime.TimeDelta(minutes=OnOffOnTime)
obs_count = 0
doCal = doFirstCal
doPointing = doFirstPointing
project_obs = 0
old_catalog_name = 'dummy'
fullcat = '/home/astro-util/projects/15B287_operator/15B287_operator.cat'

Configure(config_1)

while project_obs < 100:
    mycat,altcal = select_my_catalog()
    if mycat == old_catalog_name:
        print 'SAME CATALOG HAS BEEN SELECTED: Using FULL catalog'
        mycat = fullcat
        altcal = '3C309_1'
    old_catalog_name = mycat
    c = Catalog(mycat)
    sources = c.keys()
    for source in sources:
        doBalance = True
        newPeak = True
        calibrator = c[source]["calibrator"]
        n_obs = int(float(c[source]["n_obs"]))
        obs_left = obs_per_source-n_obs
        obs_ok = obs_left > 0
        t_now = Now()
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
        else:
            t_ok = False

        source_ok = t_ok and obs_ok

        if source_ok:
            if doPointing == True:
                #check the calibrator is above the horizon
                if h.GetRise(calibrator)>t_now:
                    myCal = altcal #circumpolar alternative
                    print 'Calibrator %s is too low: Using %s' %(calibrator,altcal)
                else:
                    myCal = calibrator
                if obs_count == 0:
                    AutoPeakFocus(myCal)
                    #Break("Check Peak and Focus")
                else:
                    AutoPeak(myCal)
                Configure(config_1)
                doBalance = True
                doPointing = False

            if doCal:
                Slew(myCal)
                Balance()
                print 'Calibration scans (OnOff) :%s ' %(myCal)
                OnOff(myCal,myOff,120.0)
                doCal = False
                doBalance = True

            for i in range(obs_left):
                t_now = Now()   #check time ok again
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

                if t_ok:
                    if peak_near_source and newPeak:
                        Slew(source)
                        AutoPeak()
                        Configure(config_1)
                        newPeak = False
                        doBalance = True
                    if doBalance:
                        Slew(source)
                        Balance()
                        doBalance = False

                    Comment("Starting on-source scan")
                    Track(source,None,scanTime)
                    Comment("Starting off-source scan")
                    Track(source,None,scanTime,fixedOffset=myOff)
                    Comment("Starting on-source scan")
                    Track(source,None,scanTime)
                    obs_count = obs_count + 1
                    obs_tot = obs_per_source+1-obs_left+i
                    print '%s: OBS COMPLETE = %s/%s' %(source,obs_tot,obs_per_source)
                    update_my_catalogs(source,obs_tot)

                    if obs_count % peak_every == 0:  #Cal/pointing interval
                        doCal = True
                        doPointing = True
        if source_ok and mycat == fullcat:
            break
    project_obs = project_obs+1
