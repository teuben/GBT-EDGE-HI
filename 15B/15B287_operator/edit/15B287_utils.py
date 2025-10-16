from mx import DateTime
from tempfile import mkstemp
from shutil import move
from os import remove, close
from subprocess import call

def update_my_catalogs(source_update, n_obs_update):
    print 'Updating Catalogs'
    mypath = '/home/astro-util/projects/15B287_operator/'
    source=source_update
    allcats = [mypath+'15B287_LST_5_9.cat',
                     mypath+'15B287_LST_0_5.cat',
                     mypath+'15B287_LST_9_13.cat',
                     mypath+'15B287_LST_13_17.cat',
                     mypath+'15B287_LST_17_21.cat',
                     mypath+'15B287_operator.cat']
    for mycat in allcats:
        fh, abs_path = mkstemp()
        with open(abs_path,'w') as new_file:
            with open(mycat) as old_file:
                for line in old_file:
                    columns = line.split()
                    if len(columns) >= 6:
                        if columns[0] == source:
                            columns[6] = str(int(float(n_obs_update)))
                            new_line = ' \t'.join(columns)+'\n'
                            new_file.write(new_line)
                        else:
                            new_file.write(line)
                    else:
                        new_file.write(line)
        close(fh)
        remove(mycat)
        move(abs_path, mycat)
        call(['chmod','777',mycat])

def select_my_catalog():
    print 'INFO: Selecting Catalog'
    LST = GetLST()
    mypath = '/home/astro-util/projects/15B287_operator/'
    if LST >= 0 and LST <= 5:
        mycat = mypath+'15B287_LST_0_5.cat'
        Comment("INFO: Using Catalog for LST 0-5")
        altcal = "3C147"
    if LST > 5 and LST <= 9:
        mycat = mypath+'15B287_LST_5_9.cat'
        Comment("INFO: Using Catalog for LST 5-9")
        altcal = "3C249_1"
    elif LST > 9 and LST <= 13:
        mycat = mypath+'15B287_LST_9_13.cat'
        Comment("INFO: Using Catalog for LST 9-13")
        altcal = "3C249_1"
    elif LST > 13 and LST <= 17:
        mycat = mypath+'15B287_LST_13_17.cat'
        Comment("INFO: Using Catalog for LST 13-17")
        altcal = "3C309_1"
    elif LST > 17 and LST < 24: #and LST <= 21:   #21 nominally
        mycat = mypath+'15B287_LST_17_21.cat'
        Comment("INFO: Using Catalog for LST 17-21")
        altcal = "3C309_1"
    else:
        mycat = mypath+'15B287_operator.cat'
        altcal = "3C309_1"
        Comment("WARNING: Using Full Catalog - WARNING!")
    return mycat,altcal
