# Installing GBT-EDGE-HI

The edge_hi.py script is all we have now. Type

      ./edge_hi.py -h

to get help. Makefile has benchark examples.

##  1. Add dysh to your environment

Covered in other places.

##  2. Get benchmark data

1. Grab sdfits_edge.tar, untar it. It will create an "sdfits" directory
and thus mimics the /home/sdfits at GBO.

The 2015 data are stored differently as a "sdfits/data" subdirectory with
only one of the 3 original IF's. (ifnum=1)

2. set the SDFITS_DATA environment variable to the just created "sdfits" directory

##  3. Run benchmarks

The Makefile has the recipe for a good 2015 and 2025 dataset:

      make bench0
      NGC3815,edge2015,3667.7,1.96,2.19,8.78,0.17,8.78,0.17,3367.7,3967.7,False EDGE_PYDB
      24.56user 2.33system 0:27.00elapsed 99%CPU

and

      make bench1
      UGC10972,edge2025,4652.0,3.71,2.39,7.86,0.11,7.96,0.11,4402.0,4902.0,False EDGE_PYDB
      5.94user 0.63system 0:06.68elapsed 98%CPU



