# Comments on the 2015 data reduction

- 117 galaxies in 39 sessions, numbered 1 - 41 (2 and 7 are skipped)

For HI F0=1.420405751786, but the data were taken with F0=1.395, so
a correction is needed.

One hack is to use the patch_restfreq.py script.  Recent versions of dysh
support setting the retfreq in a spectra, we can also set it using sdf["RESTFREQ"],
but this will apply all rows in the BINTABLE.

- BW = 100 MHz; 32768 channels; channels 0.644 km/s at HI
     
- GPS at 1.381 GHz (8300 km/s) is intermittent
      - currently those scans are removed (about 10%)
      - subscan (integration) flagging can improve, but needs algorithm (TBD)
 
- disk space:
  - just the "B" files take 43GB, if the full set, 3x that value

