
ONT   = OMP_NUM_THREADS=1
TIME  = /usr/bin/time

URL5  = https://github.com/tonywong94/edge_pydb

.PHONY : help

## help:      This Help
help : Makefile
	@sed -n 's/^##//p' $<

## new:       run pipeline and make new index 
new:
	./edge_hi.py > edge_hi.log
	./mk_index > index.html

#       tabrows is in NEMO
## new2:      sorted gals.pars2 (needs NEMO's tabrows)
new2:
	tabrows gals.pars | sort > gals.pars2

SEQ = 99
## summary:   make summarylogs file, needs SEQ=
summary:
	./mk_summary.py $(SEQ) > summarylogs/AGBT25A_474_$(SEQ).summary

## edge_pydb: get the edge_pydb
edge_pydb:
	git clone $(URL5)

## csv:     create the good looking CVS
csv:
	@awk '{print $$1}' edge_hi.log | ./latest_by_key.sh


## bench0:    benchmark NGC3815 from 2015 data
bench0:
	$(ONT) $(TIME) ./edge_hi.py --mode 0 --flux NGC3815 --batch

## bench1:    benchmark UGC10972 from 2025 data
bench1:
	$(ONT) $(TIME) ./edge_hi.py --mode 1 --flux UGC10972 --batch

## bench2:    benchmark U11578 from 2004 data
bench2:
	$(ONT) $(TIME) ./edge_hi.py --mode 2 --flux U11578 --batch
