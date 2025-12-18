# Comments on the 2025 data reduction

- Project ID:   AGBT25A_474

- 43 in total
     - 7 non-detections (to be confirmed)
     - 7 weak (to be confirmed)
     - one in common with 2015 data (NGC 2xxx, right smack with GPS)

- BW = 187.5 MHz; 32768 channels; channels 1.208 km/s at HI
     
- F0 = 1.42041 (HI line), but Fsky is different per observation
  to make the galaxy roughly come out in the center of the band

- GPS at 1.381 GHz (8300 km/s) is intermittent
      - currently those scans are removed (about 10%)
      - subscan (integration) flagging can improve, but needs algorithm (TBD)
      - data within 1000 km/s can be affected
 
- disk space:  the single IF raw data is in 7 sessions, and take up 9.7 GB
