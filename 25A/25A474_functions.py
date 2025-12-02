from mx import DateTime
from tempfile import mkstemp
from shutil import move
from os import remove, close
from subprocess import call
import re
from astropy.coordinates import EarthLocation, SkyCoord, AltAz
from astropy.time import Time
import astropy.units as u
from datetime import datetime

def update_my_catalogs(source_update, n_obs_update):
    print 'Updating Catalogs'
    mypath = '/home/astro-util/projects/25A474/'
    source=source_update
    allcats = [mypath+'targets_s1.cat',
                     mypath+'targets_s2.cat',
                     mypath+'targets_s3.cat',
                     mypath+'targets_s4.cat',
                     mypath+'targets.cat']
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
        call(['chmod', '777', mycat])


def select_my_catalog():
    print 'INFO: Selecting Catalog'
    LST = GetLST()
    mypath = '/home/astro-util/projects/25A474/'
    if LST >= 23 or LST <= 6:
        mycat = mypath+'targets_s1.cat'
        Comment("INFO: Using Catalog for LST 0-6 (S1)")
        altcal = "3C147"
    elif LST > 6 and LST <= 13:
        mycat = mypath+'targets_s2.cat'
        Comment("INFO: Using Catalog for LST 6-13 (S2)")
        altcal = "3C227"
    elif LST > 13 and LST <= 19:
        mycat = mypath+'targets_s3.cat'
        Comment("INFO: Using Catalog for LST 13-19 (S3)")
        altcal = "3C309_1"
    elif LST > 19 and LST < 23: 
        mycat = mypath+'targets_s4.cat'
        Comment("INFO: Using Catalog for LST 19-24 (S4)")
        altcal = "3C309_1"
    else:
        mycat = mypath+'targets.cat'
        altcal = "3C309_1"
        Comment("WARNING: Using Full Catalog - WARNING!")
    return mycat, altcal


def get_altitude(source_ra, source_dec, obs_time):
    obs_time = obs_time.date + ' ' + obs_time.time
    print("sanity check:::::", obs_time)
    # Based on GBT location
    GBT = EarthLocation(lat="38d25m59.236s", lon="-79d50m23.406s", height=807.43*u.m)
    coord = SkyCoord(ra=source_ra, dec=source_dec, unit=(u.deg, u.deg), frame="icrs")

    aa = AltAz(location=GBT, obstime=obs_time)#, format=u'datetime')
    altaz = coord.transform_to(aa)

    print "ALT:", altaz.alt
    return altaz.alt.value
