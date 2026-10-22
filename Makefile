
ONT   = OMP_NUM_THREADS=1
TIME  = /usr/bin/time
SDIR  = /home/sdfits
PID   = AGBT26A_644
SEQ   = 01
-include SEQ

URL5  = https://github.com/tonywong94/edge_pydb
URL6  = https://github.com/tonywong94/edge_hispec/
URL7  = https://gitlab.com/SoFiA-Admin/BusyFit

PID  = AGBT26A_644
WDIR = /users/rmaddale/Weather/ArchiveCoeffs
SDIR = /home/sdfits


.PHONY : help

## help:        This Help
help : Makefile
	@sed -n 's/^##//p' $<

## new:         run pipeline and make new index 
new:
	./edge_hi.py > edge_hi.log
	./mk_index > index.html

#       tabrows is in NEMO
## new2:        sorted gals.pars2 (needs NEMO's tabrows)
new2:
	tabrows gals.pars | sort > gals.pars2

## summary:     make summarylogs file, needs SEQ=
summary:
	./mk_summary.py $(SEQ) > summarylogs/$(PID)_$(SEQ).summary

REM = teuben@lma.astro.umd.edu:/n/lma1/teuben/
## rsync:        rsync to REM=$REM and SEQ=$SEQ
rsync:
	@echo rsync to REM=$(REM) and SEQ=$(SEQ)
	du -sh $(SDIR)/$(PID)_$(SEQ)
	@echo rawdata SEQ=$(SEQ)
	-rsync -ahv --bwlimit=8000 $(SDIR)/$(PID)_$(SEQ) $(REM)/GBTRawdata



## astrid:   make astridlogs for SEQ=$SEQ
astrid:
	(cd astridlogs; getastridlog $(PID)_$(SEQ))
	@echo git add           astridlogs/$(PID)_$(SEQ)_log.txt
	@echo git commit -m new astridlogs/$(PID)_$(SEQ)_log.txt

REM = teuben@lma.astro.umd.edu:/n/lma1/teuben/
## rsync:    rsync to REM=$REM and SEQ=$SEQ
rsync:
	@echo rsync to REM=$(REM) and SEQ=$(SEQ)
	du -sh $(SDIR)/$(PID)_$(SEQ)
	@echo rawdata SEQ=$(SEQ)
	-rsync -ahv --bwlimit=8000 $(SDIR)/$(PID)_$(SEQ) $(REM)/GBTRawdata

## edge_pydb:   get the edge_pydb
edge_pydb:
	git clone $(URL5)

## edge_hispec: get the edge_hispec (private)
edge_hispec:
	git clone $(URL6)

## BusyFit:     get the BusyFit repo
BusyFit:
	git clone $(URL7)

## csv:         create the good looking CVS
csv:
	@awk '{print $$1}' edge_hi.log | ./latest_by_key.sh


## bench0:      benchmark NGC3815 from 2015 data
bench0:
	$(ONT) $(TIME) ./edge_hi.py --mode 0 --flux NGC3815 --batch

## bench1:      benchmark UGC10972 from 2025 data
bench1:
	$(ONT) $(TIME) ./edge_hi.py --mode 1 --flux UGC10972 --batch

## bench2:      benchmark U11578 from 2004 data (dysh test)
bench2:
	$(ONT) $(TIME) ./edge_hi.py --mode 2 --flux U11578 --batch
