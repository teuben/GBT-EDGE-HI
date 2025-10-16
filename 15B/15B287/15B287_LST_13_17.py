execfile("/home/astro-util/projects/15B287/15B287_config.py")
Catalog("/home/astro-util/projects/15B287/15B287.cat")
Catalog(fluxcal)
Catalog(lband_pointing)
Configure(config_1)

# ---------------------------------------
# This is for LST between 13 and 17 hours
# ---------------------------------------

# First calibration

ptg_source = "1331+3030" # RA, dec = 13:31:08.2879 +30:30:32.958
Slew(ptg_source)
AutoPeakFocus(ptg_source)
Break("Please check pointing and focus")
Configure(config_1) #always reconfigure after AutoPeak

cal_source = "3C286" # RA, dec = 13:31:08.288 +30:30:32.96
Slew(cal_source)
Balance()
OnOff(cal_source,Offset("J2000",1.0,0.0,cosv=True),120.0) # 2 min On+Off

# First iteration

source="NGC5000"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC5406"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC5485"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC5520"
Slew(source)
AutoPeak()
Break("Please check pointing")
Configure(config_1) #always reconfigure after AutoPeak
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC5657"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC5784"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

# --------------------------------------------------------------

# Second calibration

ptg_source = "1347+1217" # RA, dec = 13:47:33.3616 +12:17:24.238
Slew(ptg_source)
AutoPeakFocus(ptg_source)
Break("Please check pointing and focus")
Configure(config_1) #always reconfigure after AutoPeak

cal_source = "3C286" # RA, dec = 13:31:08.288 +30:30:32.96
Slew(cal_source)
Balance()
OnOff(cal_source,Offset("J2000",1.0,0.0,cosv=True),120.0) # 2 min On+Off

# Second iteration

source="NGC5000"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC5406"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC5485"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC5520"
Slew(source)
AutoPeak()
Break("Please check pointing")
Configure(config_1) #always reconfigure after AutoPeak
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC5657"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC5784"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off
