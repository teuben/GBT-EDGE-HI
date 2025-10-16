execfile("/home/astro-util/projects/15B287/15B287_config.py")
Catalog("/home/astro-util/projects/15B287/15B287.cat")
Catalog(fluxcal)
Catalog(lband_pointing)
Configure(config_1)

# ---------------------------------------
# This is for LST between 5 and 9 hours
# ---------------------------------------

# First calibration

ptg_source = "0542+4951" # RA, dec =  05:42:36.1379 +49:51:07.233
Slew(ptg_source)
AutoPeakFocus(ptg_source)
Break("Please check pointing and focus")
Configure(config_1) #always reconfigure after AutoPeak

cal_source = "3C147" # RA, dec = 05:42:36.13   +49:51:07.2
Slew(cal_source)
Balance()
OnOff(cal_source,Offset("J2000",1.0,0.0,cosv=True),120.0) # 2 min On+Off

# First iteration

source="NGC2410"
Slew(source)
Balance()
for i in range(3): # 42 min total
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="UGC04280"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC2730"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC2880"
Slew(source)
AutoPeak()
Break("Please check pointing")
Configure(config_1) #always reconfigure after AutoPeak
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC2916"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC3687"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

# --------------------------------------------------------------------------

# Second calibration

ptg_source = "0555+3948" # RA, dec =  05:55:30.8056 +39:48:49.165
Slew(ptg_source)
AutoPeakFocus(ptg_source)
Break("Please check pointing and focus")
Configure(config_1) #always reconfigure after AutoPeak

cal_source = "3C161" # RA, dec = 06:27:10.00   -05:53:07.0
Slew(cal_source)
Balance()
OnOff(cal_source,Offset("J2000",1.0,0.0,cosv=True),120.0) # 2 min On+Off

# Second iteration

source="NGC2410"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="UGC04280"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC2730"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC2880"
Slew(source)
AutoPeak()
Break("Please check pointing")
Configure(config_1) #always reconfigure after AutoPeak
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC2916"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off

source="NGC3687"
Slew(source)
Balance()
for i in range(3):
    OnOff(source,Offset("J2000",1.0,0.0,cosv=True),420.0) # 7 min per On+Off
