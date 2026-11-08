# todo for July 8 meeting

1.  sample for new GBT data [~done; eltha]
2.  flux table [mostly later]
3.  radial distribution of gas
    - forward modeling + MC (Di Wen)
    - fit I(v) to busyfunction, invert using V(R) from URC

- edge_hi.py               new  "--spike N" (N=1,2,3,4 but 0 is default) to pick a despiker
                           bug wih NaN?
			   dish vs. gbtidl can be done better
			   [Enora?   check a spike version from 2025;   "--spike 4" ]  cf. flux?
- gals/hi_surveys          final tinkering done. still manual labor needed [eltha]
                           submitted now (Jun 24) as GBT26A-644
- flux.py                  some issues with V axis, but tabcog works   [dysh bug ?]
- tabcog                   alternative flux via NEMO [peter]

  
- profile/hi_profile.py    forward modeling
                           needs option to reload another model

- What are good SNR examples from 2015 and 2025, and VK3 ?
  - example of 1, 2 and 3 peak profiles
  - can 3 peak deal with busyfunction? [peter]

- Example forward modeling  using hi_profile.py 
  

# Good SNR ratio cases

Note:   we also need channel separation and resolution (in km/s) in our table

## Visually


NGC0991    edge2025  18.23 0.07  84
UGC08733   edge2025  17.03 0.12 188
NGC0681    edge2025  17.88 0.11 370
VV488NED02 edge2025  15.43 0.13 581

## Via tabcog:

NGC0991    edge2025  18.22 0.07  84  3  3.1   
NGC0991    edge2025  18.23 0.06  89  0  4.4  1565-1598=33     90%
                     18.13 0.07  87  0  4.8  dw=100
UGC08733   edge2025  17.04 0.11 190  0  5.9  3 peaks, or missing HI? 2242-2197=45 2385-2433=48
NGC0681    edge2025  17.84 0.11 370  0  4.4  1554-1597=43    1939-1986=47
                     18.09 0.11 370  0  4.6
VV488NED02 edge2025  15.51 0.14 588: 0  4.3  interacting
NGC2805    edge2015  69.14 0.05 116  0  3.4  1694-1637=57  1748-1806=58
                     68.76 0.05 115  0  3.8  dv=125 dw=150
NGC3994    edge2015  34.54 0.08 349  0  4.0  strong low vel wing
NGC2604    edge2015  17.74 0.06 161  0  3.8

## Busy Fits

150.0 300.0

./edge_hi.py  --flux  --mode 15  --smooth 0  NGC2805 --busy

./edge_hi.py  --flux  --smooth 0 NGC0681 --busy --dw 250

noplot

./edge_hi.py  --flux  --smooth 0 NGC0991 --busy --dw 100
2nd time gave plot


## Baselines

Would be nice to describe the raw baselines, as there are several types. We limit it to 0 to 10,000 km/s,
and we assume the GPS RFI has been removed. For galaxies < 6000 km/s we often don't bother taking it out
as it does not appear to influence the baselines

1. flat
2. slight undulations, not impeding source detection; use (MAX-MIN)/RMS as parameter?
3. stronger undulations
4. very bad baselines, due to ON/OFF ?
