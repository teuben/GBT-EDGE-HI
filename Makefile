#


#       return pipeline and make new index 
new:
	./edge_hi.py > edge_hi.log
	./mk_index > index.html

#       tabrows is in NEMO
new2:
	tabrows gals.pars | sort > gals.pars2

SEQ = 99
summary:
	./mk_summary.py $(SEQ) > summarylogs/AGBT25A_474_$(SEQ).summary
