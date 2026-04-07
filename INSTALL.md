# Installing GBT-EDGE-HI

## 0. Source code

Is on github.  git@github.com:teuben/GBT-EDGE-HI

## Running 

The edge_hi.py script is all we have now. Type

      ./edge_hi.py -h

to get help. Makefile has benchark examples. See below.


The basic outline of the pipeline is as follows

1. grab the sessions and scans needed to co-add spectra for a given object (see the galsXX.pars file)
2. calibrate (default in flux mode) so they can be co-added 
3. align data and set frame (in that order!) so they can be co-added
4. co-add and average spectra
5. optionall patch the NaN's (at multiples of 8192)
6. Grab spectrum using the --dv and --dw: from vlsr-dv-dw to  vlsr+dv+dw
7. Smooth spectrum (allow it to average over NaN's)
7. Fit and subtract baseline in the two dw portions


##  1. Add dysh to your environment

Covered in other places.

##  2. Get benchmark data

Grab `sdfits_edge.tar`, untar it. It will create an "sdfits" directory
and thus mimics the /home/sdfits at GBO. See /lma1/teuben/GBTRawdata/sdfits_edge.tar

Note, the 2015 data are stored differently in the "sdfits/data" subdirectory with
only one of the 3 original IF's. (ifnum=1). The full data can be used if the --full flag
is used.

Set the SDFITS_DATA environment variable to the just created "sdfits" directory

##  3. Run benchmarks

The Makefile has the recipes for a good 2015 and 2025 dataset.

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

## 4. Examples and some remaining issues

Some commands and exposing dysh issues

1. Default 2025 data with flux scaling to Jy.km/s, but showing channels instead of km/s.

      ./edge_hi.py UGC10972 --flux --chan

   this shows a negative spike right in the middle of the galaxy signal. Zooming in Figure 2 shows this is channel
   16393, i.e. the one but last channel in the 2nd "bank" of 8k channels.

   Turns out the alignment (needed to stack doppler shifted spectra) is the culprit. The following command doesn't show
   this spike
   
      ./edge_hi.py UGC10972 --flux --chan --align

   [solved - to.align() defaults to an fft method, it needs to be interpolate]

3. Smoothing the reference can introduce spikes too:

      ./edge_hi.py UGC10972 --flux --chan --align --smoothref 4

   Since Figure 1 is smoothed (default by 3 channels), you can't use it. Zoom into Figure 1, or use --smooth 0 to get
   Figure 1 in raw channels. Either way, it shows that smoothref introduces quite a few spikes.

   Smoothref also introduces a lot of new NaN's near the board boundaries, so the smooth is not using the nan treatment
   we use in our script.

4. The 2015 (older ACS) data have true spikes in the raw TP data. But because often that channel is one off between the
   ON and OFF, the resulting spectrum has a alternating +/- spike. See for example

      ./edge_hi.py --mode 15 NGC3815 --flux --chan --smooth 0

   where again --smooth 0  is needed to see the spikes in Figure 1.

   For this case the following channels have TP spikes:  5819,5820,8992,8993,9094,9095,9096,9199,9200,8073

   It should be noted some of the spikes have an actual structure, which makes spike detection harder.

5. Waterfall plots can be useful, but the --water flag doesn't allow you to play qith the color stretch. With the
   --avechan a fits file is produced for each session. For example for the UGC10972 case

      ./edge_hi.py UGC10972 --water --avechan 1,15400,17400

   which in this case produces a fits file `UGC10972_water_1.fits` of dimension 360 (integrations) x 2000 (channels).


6. Example of running the whole pipeline

      ./edge_hi.py ---all --batch --mode 25 --flux --frame icrs > edge_hi.log
      grep EDGE_PYDB edge_hi.log | awk '{print $1}'
