# Installing GBT-EDGE-HI

The edge_hi.py script is all we have now. Type

      ./edge_hi.py -h

to get help. Makefile has benchark examples. See below.

##  1. Add dysh to your environment

Covered in other places.

##  2. Get benchmark data

1. Grab `sdfits_edge.tar`, untar it. It will create an "sdfits" directory
and thus mimics the /home/sdfits at GBO.

Note, the 2015 data are stored differently as a "sdfits/data" subdirectory with
only one of the 3 original IF's. (ifnum=1). The full data can be used if made
availabkle, and need the --full flag.

2. set the SDFITS_DATA environment variable to the just created "sdfits" directory

##  3. Run benchmarks

The Makefile has the recipe for a good 2015 and 2025 dataset.

Bench0 runs a 2015 dataset, which has the ON-OFF-ON triplets and uses `getsigref`

      # needs AGBT25A_474_01/
      make bench0
      NGC3815,edge2015,3667.7,1.96,2.19,8.78,0.17,8.78,0.17,3367.7,3967.7,False EDGE_PYDB

Bench1 runs a 2025 dataset, which has the ON-OFF pairs and uses `getps`

      # needs data/AGBT15B_287_01.fits 
      make bench1
      UGC10972,edge2025,4652.0,3.71,2.39,7.86,0.11,7.96,0.11,4402.0,4902.0,False EDGE_PYDB

Bench2 runs a case from the dysh `hi-survey` notebook (2016 data)

      # needs AGBT04A_008_02.raw.acs.fits
      make bench2
      U11578,survey2004,4570.0,-0.25,26.53,16.72,0.16,16.72,0.16,4495.0,4645.0,False EDGE_PYDB

Examples for `release-1.1` (April 2026)


| machine/CPU  |   bench0  | bench1 | bench2 |
| ------------ | --------- | ------ | ------ |
| P14s / AMD 370       | 25.02u 2.39s 0:27.54e 99%CPU | 5.81u 0.62s 0:06.56e 98%CPU  | - |
| lma / AMD EPYC 7302  | 24.75u 5.94s 0:37.90e 80%CPU | 12.26u 2.07s 0:21.72e 66%CPU | 7.71u 0.65s 0:09.22e 90%CPU |
| d76 / iU7 155H       | 17.38u 4.11s 0:21.52e 99%CPU |  8.45u 1.48s 0:09.97e 99%CPU | 5.13u 0.39s 0:05.71e 96%CPU |

## 4. Issues

Some commands and exposing dysh issues

1. Default 2025 data with flux scaling to Jy.km/s

      ./edge_hi.py UGC10972 --flux --chan

   this shows a negative spike right in the middle of the galaxy signal. Zooming in Figure 2 shows this is channel
   16393, i.e. the one but last channel in the 2nd "bank" of 8k channels.

2. Turns out the alignment (needed to stack doppler shifted spectra) is the culprit. The following command doesn't show
   this spike
   
      ./edge_hi.py UGC10972 --flux --chan --align

3. Smoothing the reference can introduce spikes:

      ./edge_hi.py UGC10972 --flux --chan --align --smoothref 4

   Since Figure 1 is smoothed (default by 3 channels), you can't use it. Zoom into Figure 1, or use --smooth 0 to get
   Figure 1 in raw channels. Either way, it shows that smoothref introduces quite a few spikes.

   Smoothref also introduces a lot of new NaN's near the board boundaries, so the smooth is not using

4. The 2015 (older ACS) data have true spikes in the raw TP data. But because often that channel is one off between the
   ON and OFF, the resulting spectrum has a alternating +/- spike. See for example

      ./edge_hi.py --mode 15 NGC3815 --flux --chan --smooth 0

   where again --smooth 0  is needed to see the spikes in Figure 1.
