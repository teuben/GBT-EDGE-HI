execfile("/home/astro-util/projects/15B287/15B287_config.py")
Catalog("/home/astro-util/projects/15B287/15B287.cat")
Catalog(fluxcal)
Catalog(lband_pointing)
Configure(config_1)

# ---------------------------------------
# This is for LST between 17 and 21 hours
# ---------------------------------------

# First calibration

ptg_source = "1602+3326" # RA, dec = 16:02:07.2634 +33:26:53.072
Slew(ptg_source)
AutoPeakFocus(ptg_source)
Break("Please check pointing and focus")
Configure(config_1) #always reconfigure after AutoPeak

cal_source = "3C348" # RA, dec = 16:51:08.3   +04:59:26.0
Slew(cal_source)
Balance()
OnOff(cal_source,Offset("J2000",1.0,0.0,cosv=True),120.0) # 2 min On+Off

# First iteration

source="NGC5876"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="UGC10123"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC6155"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC6310"
Slew(source)
AutoPeak()
Break("Please check pointing")
Configure(config_1) #always reconfigure after AutoPeak
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC6497"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC6762"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

# ---------------------------------------------------------------------

# Second calibration

ptg_source = "1745+1720" # RA, dec = 17:45:35.2081 +17:20:01.423
Slew(ptg_source)
AutoPeakFocus(ptg_source)
Break("Please check pointing and focus")
Configure(config_1) #always reconfigure after AutoPeak

cal_source = "3C353" # RA, dec = 17:20:29.5   -00:58:52.0
Slew(cal_source)
Balance()
OnOff(cal_source,Offset("J2000",1.0,0.0,cosv=True),120.0) # 2 min On+Off

# Second iteration

source="NGC5876"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="UGC10123"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC6155"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC6310"
Slew(source)
AutoPeak()
Break("Please check pointing")
Configure(config_1) #always reconfigure after AutoPeak
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC6497"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC6762"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off
