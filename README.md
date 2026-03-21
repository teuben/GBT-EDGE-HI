# GBT-EDGE-HI

HI survey of EDGE galaxies using the GBT.   Started with **AGBT15B_287**, where 113 galaxies were
observed in a modified PositionSwitch using ON-OFF-ON and a corresponding getsigref
procedure. The original GBTIDL procedure can be done with `edge.pro`.


Utomo, Dyas	GBT/15B-287	HI Follow-up Observations of the EDGE-CALIFA Survey	125.5h


The followup project code is **AGBT25A_474**, where 43 galaxies were observed. Only one
case had overlap with the 2015 data, NGC2918, but this galaxy doesn't seem to have much,
if any, signal, plus there is a GPS nearby in some of the data.

Old observing scripts at GBO:

  * /home/astro-util/projects/15B287_operator
  * /home/astro-util/projects/15B287

these have been recorded in our `15B` directory.  An example to reduce these for NGC 2805
are in the `examples/` directory

## Procedure

The python based `dysh` package is used here for reduction. The gals15.pars  and gals25.pars text files
are used to set basic parameters: which session, which scans, the v0 (center of galaxy window),
dv (half width of galaxy) and dw (width of each half of the baseline on either side. A
resulting spectrum with width 2.dv + 2.dw is then extracted, plotted, baseline subtracted
and written to a text file.

The ON-OFF-ON in 2015 is processed with getsigref(), the ON-OFF in 2025 with getps().

Since some galaxies appear in multiple sessions, co-adding needs to be in a common velocity
frame (we choose "icrs" or solar system barycenter) and opacity corrected Jy. A flux in Jy.km/s
is computed 

## Installation

Install [dysh](https://github.com/GreenBankObservatory/dysh) in your choice of a (virtual) environment.

There is an example `install_dysh` script for this as well.

If you want the dysh profile (see test1.py),

```
   ipython profile create dysh
   cp 90-dysh.py ~/.ipython/profile_dysh/startup/
```

after which

```
   ipython --profile=dysh
```

will start the poor-man's version of dysh. See comments in `test1.py`

Normally the command

```
   dysh
```

will get you an interactive session.

### dyshp

There is also an alternative install that Peter used while developing dysh:
https://github.com/teuben/dyshp


## Example

Make sure your data is in the `$SDFITS_DATA` directory (or use /home/sdfits).
If you use $DYSH_DATA, they
can also be located in the `$DYSH_DATA/sdfits` directory



```
f1=dysh_data('AGBT15B_287_19')
sdf1 = GBTFITSLoad(f1)
sdf1.filename
```

but for now the following
is a bug/feature (see https://github.com/GreenBankObservatory/dysh/issues/740)

```
unset DYSH_DATA
export SDFITS_DATA=/home/teuben/GBT/dysh_data/sdfits
dysh
  f2=dysh_data('AGBT15B_287_19')
  sdf2=GBTOffline('AGBT15B_287_19')
  sdf2.filename

  f1=dysh_data('AGBT15B_287_19', dysh_data='/home/teuben/GBT/dysh_data/')

```

### Interference

Some fraction of data has RFI: the signal comes from a GPS L3
signal, which transmits to a GPS tracking station in
Maryland. Unfortunately, the GBT falls within the GPS signal's
footprint, so it may be a frequent occurrence in our data. The GPS L3 intermsignal
has a center frequency of 1381.05 MHz, or around 8300 km/s.

## Comparing with GTBIDL

```
    gbtidl
    .compile edge
    tic
    filein,'AGBT15B_287_01.B.fits'
    edge, 10,18
    toc

    tic
    filein,'AGBT15B_287_01.B.fits'
    edge, 10,12
    toc

    tic
    filein,'AGBT15B_287_01.B.fits'
    edge, 10,15
    toc


    
    fileout,'ngc3815_gbtidl.fits'
    keep
```

   -> 41.7 min

2.2sec vs. 0.90 sec vs. 1.50 sec
   
## GBT links

DSS project page: https://dss.gb.nrao.edu/project/GBT25A-474

Explanation of Grades: https://greenbankobservatory.org/portal/gbt/proposing/#panel-scores-and-groups

Schools and Workshops: https://greenbankobservatory.org/science/gatherings/

Steps for observation preperation: https://greenbankobservatory.org/portal/gbt/proposing/#next-steps-for-accepted-proposals

GBT Infrastructure Work: https://greenbankobservatory.org/portal/gbt/proposing/#gbt-infrastructure-work

Receiver schedule: https://dss.gb.nrao.edu/receivers

TAC report (including LST pressure plots): https://science.nrao.edu/observing/proposal-types/tac-reports/25a-tac-report

Science program: https://science.nrao.edu/science/science-program/2025a

### Important directories

* /home/astro-util/projects/25A474  : observing file, catalogs etc.
