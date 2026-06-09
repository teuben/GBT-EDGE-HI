#

t0.n:
	tabcols edge_califa.csv    2 |  tr '[:lower:]' '[:upper:]' | grep -vi name | sort > t0.n
	@wc -l t0.n

t0e.n:
	tabcols ecalifa_global.csv 2 |  tr '[:lower:]' '[:upper:]' | grep -vi name | sort > t0e.n
	@wc -l t0e.n

t0l.n:
	tabcols ecalifa_leda.csv   3 |  tr '[:lower:]' '[:upper:]' | grep -vi name | sort > t0l.n
	@wc -l t0l.n

t1.n:
	tabcols edge_leda.csv      1 |  tr '[:lower:]' '[:upper:]' | grep -vi name | sort > t1.n
	@wc -l t1.n

t1e.n:
	tabcols ecalifa_leda.csv   1 |  tr '[:lower:]' '[:upper:]' | grep -vi name | sort > t1e.n
	@wc -l t1e.n

t2.n:
	tabcols iedge_v1.ecsv      1 |  tr '[:lower:]' '[:upper:]' | grep -vi name | sort > t2.n
	@wc -l t2.n

t3.n:
	tabcols edge_hiflux.csv    1 |  tr '[:lower:]' '[:upper:]' | grep -vi name | sort > t3.n
	@wc -l t3.n

t4.n:
	tabcols edge2025.csv       1 |  tr '[:lower:]' '[:upper:]' | grep -vi name | sort > t4.n
	@wc -l t3.n
