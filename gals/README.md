# Summary of catalogs

1. CALIFA has ~900 galaxies, but only ~600 were observed  [table5]
2. FAST has ~42,000 galaxies - has flux                   [table2]
3. Arecibo has ~32,000 galaxies - has flux                [table6]
4. edge and HyperLEDA [edge_leda.csv] crosscheck          [table4]
   http://atlas.obs-hp.fr/hyperleda/
5. edge and NED , 126 entries                             [table7]
6. edge_hiflux , 161 entries                              [table8]
   edge2025 , 43 entries                                  [table8a]

See also https://pages.astro.umd.edu/~bolatto/EDGE/

AMUSING: https://amusing-muse.github.io/

https://skyserver.sdss.org/dr19/VisualTools/navi?ra=41.291443&dec=-4.710761

## CALIFA_HI_sample_archive.csv :   923 entries (extended CALIFA sample)

CALIFA_name,    RA,              DEC,             Vlsr,             Final_QS,Final_NA,Final_flag_QS,Final_flag_NA,Archive_HI?
2MASSXJ22532475,343.353174258808,4.79951056351426,7350.357507551282,SF,      nonA,    1,            S,            N
...
sn2008gt,341.185099653577,-3.14926389550093,9859.889841487513,nR,nonA,1,S,N

## FAST: Table2-FASHI_extragalactic_HI_source_catalog.csv : 41742 entries

    ID_FASHI,Name,ra,dec,ra-dec_err,cz,cz_err,cz_min,cz_max,v_radio,v_radio_err,freq,freq_err,z,z_err,ell_maj,ell_min,ell_pa,W_50,W_50_err,W_20,W_20_err,F_peak,F_peak_err,S_bf,S_bf_err,S_sum,S_sum_err,rms,SNR,distance,distance_err,log10Mass,log10Mass_err 
    20230000823,J110656.76-061135.4,166.7365,-6.1932,0.0024,6802.07,0.77,6656.84,7014.73,6651.16,0.77,1388.8928,0.0037,0.022690,0.000003,3.7,3.7,0,164.01,1.55,172.62,2.32,9.05,1.79,1179.44,81.68,1046.79,81.68,1.79,20.35,98.18,4.91,9.42,0.05
    ...
    20230064309,J231825.50+651915.7,349.6063,65.3210,0.0043,20762.27,2.03,20642.11,20885.69,19417.50,2.03,1328.4063,0.0096,0.069260,0.000008,2.8,2.8,0,116.98,4.06,134.91,6.10,4.79,1.83,560.07,64.75,588.11,64.75,1.83,11.18,279.38,13.97,9.98,0.07



## ARECIBO:   a100.code12.table2.190808.csv : 31502 entries

AGCNr,Name,RAdeg_HI,DECdeg_HI,RAdeg_OC,DECdeg_OC,Vhelio,W50,sigW,W20,HIflux,sigflux,SNR,RMS,Dist,sigDist,logMH,siglogMH,HIcode
105367,........,   0.00167,   5.44333,   0.00333,   5.44250,11983,274, 39,281,  1.14,0.08,  8.1,  1.91,166.0, 2.3, 9.87,0.05,1
..
31502 332118 ........ 359.98877 4.89722 359.99084 4.90111 9207 186 4 199 1.58 0.09 9.9 2.62 126.4 2.2 9.77 0.05 1

## Veselina/hiedge_all_spectra : 568 entries

No data, just pdf files.... are these roughly the 561 "Y" entries from CALIFA_HI_sample_archive.csv?

    ls | sed s/_all_hi_spectra.pdf// | sort > /tmp/hiedge_all_spectra.tab

## iEDGE (643 entries)

Large table, has 158 columns summarizing all properties of the Califa sample. About 1.1MB.
see https://zenodo.org/records/15822433

https://zenodo.org/records/15822433/files/iedge_v1.ecsv?download=1

#  Summary Tables

## table2 (FAST)

    head -1 Table2-FASH* | tabcols - colsep=N | tabtab - offset=1
    tabcols Table2-FASH* 2,3,4,6,19,27 > table2.tab
    tabcols Table2-FASH* 2,3,4,6,19,27 | head -2 | tabcomment - > table2.tab
    tabcols Table2-FASH* 2,3,4,6,19,27 | tail +3 | sort        >> table2.tab

    # table2.tab : 41741
    #ID_FASHI ra dec cz
    20230000823 166.7365 -6.1932 6802.07
    ...
    20230042080 125.7049 -6.1691 14644.66

## table3 (GBT archival search)

    # table3.tab : 82 entries  (extracted from CALIFA_archival_search_results.csv with 3691 entries)
    #   gbt archival
    ARP118 43.7905275 -0.1778504
    ...
    UGC9837 230.965329 58.0529766

## table4 (hyperleda)

    tabcols ../edge_pydb/edge_pydb/dat_glob/external/edge_leda.csv 1,3,4,15 | head -1 | tabcomment -  > table4.tab
    tabcols ../edge_pydb/edge_pydb/dat_glob/external/edge_leda.csv 1,3,4,15 | tail +2 | sort         >> table4.tab     

    # table4.tab : 647 entries 
    #Name(1) ledaRA(3) ledaDE(4) ledaVrad(15)       [ledaHIflux(25)]
    2MASXJ01331766+1319567 23.3237175 13.3322413
    ...
    VV488NED02 344.21196 -8.9675601

## table5 (CALIFA)

    head -1 CALIFA_HI*csv | tabcols - colsep=N | tabtab - offset=1
    grep ,Y CALIFA_HI*csv | tabcols - 1,2,3,4 | sort            > table5y.tab
    grep ,N CALIFA_HI*csv | tabcols - 1,2,3,4 | sort            > table5n.tab
    head -1 CALIFA_HI*csv | tabcols - 1,2,3,4,9 | tabcomment -  > table5.tab
    tabcols CALIFA_HI*csv 1,2,3,4,9 | tail +2   | sort         >> table5.tab
    

    # table5.tab : 922 entries (from  CALIFA_HI_sample_archive.csv )
    # CALIFA_name RA DEC Vlsr
    2MASSXJ22532475 343.353174258808 4.79951056351426 7350.357507551282 N
    ...
    sn2008gt 341.185099653577 -3.14926389550093 9859.889841487513 N

## table6 (ARECIBO)

    head -1 a100.* | tabcols - colsep=N | tabtab - offset=1
    tabcols a100.code12.table2.190808.csv 1,3,4,7,8,11,19 | tabcomment - > table6.tab 

    # table6.tab : 31503 
    # AGCNr RAdeg_HI DECdeg_HI Vhelio W50 HIflux HIcode
    105367 0.00167 5.44333 11983 274 1.14 1
    ...
    332118 359.98877 4.89722 9207 186 1.58 1

## table7 (NED)

    tabcols ../edge_pydb/edge_pydb/dat_glob/external/edge_ned.csv 1,2,3,4 | head -1 | tabcomment -  > table7.tab
    tabcols ../edge_pydb/edge_pydb/dat_glob/external/edge_ned.csv 1,2,3,4 | tail +2 | sort         >> table7.tab

    # table7.tab : 126
    ARP220 233.73854 23.50314 5434
    ...
    UGC10710 256.71883 43.12219 8387

## table8 (edge_hiflux)

    tabcols ../edge_pydb/edge_pydb/dat_glob/obs/edge_hiflux.csv | head -1 | tabcols - colsep=N | tabtab - offset=1
    tabcols ../edge_pydb/edge_pydb/dat_glob/obs/edge_hiflux.csv 1,2,3,8,12 | head -1 | tabcomment -  > table8.tab
    tabcols ../edge_pydb/edge_pydb/dat_glob/obs/edge_hiflux.csv 1,2,3,8,12 | tail +2 | sort         >> table8.tab

    161 entries,  16 have BadFlag, 145 are ok
    ARP220 edge2015 5427.0 -15.3437 True
    ...
    UGC12864 shg2005 4683.0 10.6954 False

## table8a (edge2025_hiflux)

    tabcols ../edge2025.csv 1,2,3,8,12  | sort > table8a.tab

    161 entries,  16 have BadFlag, 145 are ok
    ARP220 edge2015 5427.0 -15.3437 True
    ...
    UGC12864 shg2005 4683.0 10.6954 False



# Examples comparing


## CALIFA w/ FAST

     tabdist table5y.tab table2.tab 2,3 2,3 1 1  radec=t dmin=10
     22/562  at 10"
     142     at 60"

     tabdist table5n.tab table2.tab 2,3 2,3 1 1  radec=t dmin=10
     11/361  at 10"
     42         60"

## CALIFA W/ Arecibo

     tabdist table5y.tab table6.tab 2,3 2,3 1 1  radec=t dmin=10
     84/562  at 10"
     274        60"
     
     tabdist table5n.tab table6.tab 2,3 2,3 1 1  radec=t dmin=10
     4/361   at 10"
     20         60"
     

## FAST w/ Arecibo

     tabdist table2.tab table6.tab 2,3 2,3 1 1  radec=t dmin=10 > table_26.tab
     439 matches

     # comparing flux
     tabcols table_26.tab 6,14 | tabmath - - %1/1000,%2 all > table_26_flux.tab
     tabplot table_26_flux.tab  1 2 0 16 0 16 layout=diag.layout xlab=FAST ylab=Arecibo
     # at low flux, arecibo is higher, at high flux, arecibo is lower
     # breakeven around 4 Jy.km/s
     tabmath table_26_flux.tab - 'log(%1),log(%2)' all |\
        tabplot -  1 2 -1 3 -1 3 layout=diag.layout xlab=FAST ylab=Arecibo point=2,0.1 headline="log(FLux Jy.km/s)"

     tabdist table2.tab table6.tab 2,3 2,3 1 1  radec=t dmin=100 | tabcols - 18 | sort -n > table_26_distance.tab
     tabhist table_26_distance.tab bins=80 xmin=0 xmax=80 gauss=f residual=f maxcount=200
     -> ~185 true spot-on matches. After this the 2-pt corr comes in

     # comparing W50
     tabcols table_26.tab 5,13 | tabplot - 1 2 0 800 0 800
     # large fraction with spread


## cmp

     tabcols table5y.tab  1 | sort > junk1
     # most in junk1 are in hiedge_all_spectra.tab
     # but 6 are not in junk1:
     comm -13 junk1 hiedge_all_spectra.tab
     
     CGCG97041d
     CGCG97072b
     KU0210-078
     KUG0210-078
     UGC00386
     UGC10799
