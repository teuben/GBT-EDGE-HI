pro find_astrid_sessions

  catalog = '/home/astro-util/projects/15B287_operator/15B287_operator.cat'

  openr,lun,catalog,/get_lun
  file_contents = ['']
  line = ''
  while ~eof(lun) do begin &$
     readf,lun,line &$
     file_contents = [file_contents,line] &$
  endwhile
  free_lun,lun
  start_line = (where(strmatch(file_contents,'HEAD*',/fold_case)))[0]
  file_contents = file_contents[start_line+1:*]
  idx = where(~strmatch(file_contents,'#*') and $
              strlen(strcompress(file_contents,/remove_all)) NE 0)
  file_contents = file_contents[idx]
  nlines = n_elements(file_contents)
  template = {source:'',dss:0l,astrid:0l,project:''}
  for i = 0, nlines-1 do begin &$
     line = strcompress(strsplit(file_contents[i],' '+string(9B),/extract)) &$
     if n_elements(line) GE 5 then begin &$
        info = template &$
        info.source = line[0] &$
        info.dss = long(line[4]) &$
        if n_elements(finfo) EQ 0 then finfo = info else finfo = [finfo,info] &$
     endif &$
  endfor
  uidx = uniq(finfo.source,sort(finfo.source))
  info = finfo[uidx]

  ;find antenna files
  spawn,'ls /home/gbtdata/AGBT15B_287_*/Antenna/*.fits',antenna_files,dummy
  nfiles = n_elements(antenna_files)
  astrid_template = {source:'',project:'',date:'',scan:0l}
  for i = 0, nfiles-1 do begin &$
     h = headfits(antenna_files[i]) &$
     if size(h,/type) NE 7 then goto, next_antenna &$
     source = strcompress(sxpar(h,'OBJECT'),/remove_all) &$
     project = strcompress(sxpar(h,'PROJID'),/remove_all) &$
     date    = strcompress(sxpar(h,'DATE-OBS'),/remove_all) &$
     scan    = long(sxpar(h,'SCAN')) &$
     if source NE '' AND project NE '' AND date NE '' then begin &$
        temp = astrid_template &$
        temp.source = source &$
        temp.project = project &$
        temp.date = date &$
        temp.scan = scan &$
        if n_elements(astrid) EQ 0 then astrid = temp else astrid = [astrid,temp] &$
     endif &$
     next_antenna: &$
  endfor

  ncat = n_elements(info)
  nscans = n_elements(astrid)
  for i = 0, nscans-1 do begin &$
     s = strcompress(strsplit(astrid[i].project,'_',/extract),/remove_all) &$
     s = s[n_elements(s)-1] &$
     astrid[i].project = s &$
  endfor

  template = {SOURCE:'',DSS:'',ASTRID:''}
  for i = 0, ncat-1 do begin &$
     idx = where(strmatch(astrid.source,info[i].source,/fold_case),nmatch) &$
     if nmatch NE 0 then begin &$
        sessions = astrid[idx].project &$
        sessions = sessions[uniq(sessions,sort(sessions))] &$
        if n_elements(sessions) GT 1 then sessions[0:n_elements(sessions)-2] +=',' &$
        sessions = strjoin(sessions) &$
        temp = template &$
        temp.source = info[i].source &$
        temp.DSS = strcompress(string(info[i].dss),/remove_all) &$
        temp.astrid = sessions &$
        if n_elements(final) EQ 0 then final = temp else final = [final,temp] &$
     endif &$
  endfor
  sess = long(final.dss)
  sortidx = sort(sess)
  final = final[sortidx]
  p = print_structure(final)
  print,''
  for i = 0, n_elements(p)-1 do print,p[i]

  ;now print astrid dates
  uidx = uniq(astrid.project,sort(astrid.project))
  astrid_times = {ASTRID:'',DATE_TIME:''}
  astrid_times = replicate(astrid_times,n_elements(uidx))
  astrid_times.astrid = astrid[uidx].project
  astrid_times.date_time = astrid[uidx].date
  sort = sort(long(astrid_times.astrid))
  astrid_times = astrid_times[sort]
  pa = print_structure(astrid_times)
  print,'' & print,''
  for i = 0, n_elements(pa)-1 do print,pa[i]

end
