# Flagging


2015 has a lot of spikes, which can bias the baseline, if not flux in the galaxy.

Spikes can be masked in final spectrum space (--flags), and with a good --smooth
these will be ignored in the smoothing.

For good spike removal, the --spike is not good enough, Better to add them to
the flags file.


## GPS

GPS is dominant between 1.380 and 1.382 GHz. It seems this occurs quasi-randomly
about 6% of the time,

Example analysis:

      grep -v 000000 NGC4210_water_3.tab | tabbin - > junk.tab
      tabplot3.py -i junk.tab  -l 1 
      tabmath junk.tab - 'iflt(%2,1e8,1,0)' all | sort | uniq -c

2015 results:

      gal         gps  ok   clip   %    
      NGC2410      61  704  1.5e9  8.0
      NGC3815      20  367  1.5e9  5.2
      NGC3994       8  757  1.5e9  1.0
      NGC4149_3    43  464  0.6e8  8.5
      NGC4149_13   24  229  1.0e8  9.5
      NGC4210_3    66  694  2.0e8  8.7
      a_lot      810 11886  2.0e8  6.4



3687
~2500

IC0674   7.55(0.15) @ 7507 [499]
bench0: 27.82user 3.27system 0:31.88elapsed 97%CPU 
        22.90user 2.40system 0:25.42elapsed 99%CPU
