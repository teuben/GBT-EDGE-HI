execfile("/home/astro-util/projects/15B287/15B287_config.py")
Catalog("/home/astro-util/projects/15B287/15B287.cat")
Catalog(fluxcal)
Catalog(lband_pointing)
Configure(config_1)

# ---------------------------------------
# This is for LST between 9 and 13 hours
# ---------------------------------------

# First calibration

ptg_source = "1058+0133" # RA, dec =  10:58:29.6052 +01:33:58.823
Slew(ptg_source)
AutoPeakFocus(ptg_source)
Break("Please check pointing and focus")
Configure(config_1) #always reconfigure after AutoPeak

cal_source = "3C227" # RA, dec =  09:47:46.4   +07:25:12.0
Slew(cal_source)
Balance()
OnOff(cal_source,Offset("J2000",1.0,0.0,cosv=True),120.0) # 2 min On+Off

# First iteration

source="NGC3815"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC3994"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC4149"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC4210"
Slew(source)
AutoPeak()
Break("Please check pointing")
Configure(config_1) #always reconfigure after AutoPeak
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC4644"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC4711"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

# --------------------------------------------------------------------------

# Second calibration

ptg_source = "1058+0133" # RA, dec =  10:58:29.6052 +01:33:58.823
Slew(ptg_source)
AutoPeakFocus(ptg_source)
Break("Please check pointing and focus")
Configure(config_1) #always reconfigure after AutoPeak

cal_source = "3C227" # RA, dec =  09:47:46.4   +07:25:12.0
Slew(cal_source)
Balance()
OnOff(cal_source,Offset("J2000",1.0,0.0,cosv=True),120.0) # 2 min On+Off

# Second iteration

source="NGC3815"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC3994"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC4149"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC4210"
Slew(source)
AutoPeak()
Break("Please check pointing")
Configure(config_1) #always reconfigure after AutoPeak
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC4644"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC4711"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off
