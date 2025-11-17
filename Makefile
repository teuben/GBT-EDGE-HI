#



new:
	./edge_hi.py > edge_hi.log
	./mk_index > index.html

SEQ = 99
summary:
	./mk_summary.py $(SEQ) > summarylogs/AGBT25A_474_$(SEQ).summary
