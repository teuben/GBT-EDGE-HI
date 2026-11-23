#!/usr/bin/env python
"""
Make an SDSS color cutout centered on a galaxy with a circle overlaid.

Usage:
    sdss_cutout.py NAME    [-o out.png] [--fov 10] [--diam 9]
    sdss_cutout.py RA DEC  [-o out.png] [--fov 10] [--diam 9] [--name NAME]

NAME is resolved to RA/DEC via CDS Sesame (SIMBAD/NED/VizieR), e.g. NGC5194.
RA/DEC in decimal degrees, or sexagesimal ("12:30:49.4" "+12:23:28").
FOV and circle diameter are in arcmin.
"""
import argparse
import io
import re
import sys
import urllib.parse
import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from PIL import Image

URL = "https://skyserver.sdss.org/dr18/SkyServerWS/ImgCutout/getjpeg"


def parse_coord(ra, dec):
    if ":" in ra or " " in ra.strip():
        h, m, s = [float(x) for x in ra.replace(":", " ").split()]
        ra = 15.0 * (h + m / 60 + s / 3600)
    else:
        ra = float(ra)
    if ":" in dec or " " in dec.strip():
        sign = -1 if dec.strip().startswith("-") else 1
        d, m, s = [abs(float(x)) for x in dec.replace(":", " ").split()]
        dec = sign * (d + m / 60 + s / 3600)
    else:
        dec = float(dec)
    return ra, dec


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("pos", nargs="+", metavar="NAME | RA DEC",
                   help="object name, or RA and DEC")
    p.add_argument("-o", "--out", default=None, help="output PNG")
    p.add_argument("--fov", type=float, default=10.0, help="field of view [arcmin]")
    p.add_argument("--diam", type=float, default=9.0, help="circle diameter [arcmin]")
    p.add_argument("--npix", type=int, default=1200, help="image size [pixels], max 2048")
    p.add_argument("--name", default=None, help="label for the plot title")
    # protect negative sexagesimal DEC (e.g. -05:42:40) from being seen as an option
    argv = [" " + x if re.match(r"^-\d+[: ]", x) else x for x in sys.argv[1:]]
    a = p.parse_args(argv)

    if len(a.pos) == 1:
        from astropy.coordinates import SkyCoord
        from astropy.coordinates.name_resolve import NameResolveError
        obj = a.pos[0]
        try:
            c = SkyCoord.from_name(obj)
        except NameResolveError as e:
            sys.exit(f"Could not resolve '{obj}': {e}")
        ra, dec = c.ra.deg, c.dec.deg
        if a.name is None:
            a.name = obj.replace(" ", "")
        print(f"{obj}: RA={c.ra.to_string(unit='hour', sep=':', precision=2)} "
              f"DEC={c.dec.to_string(sep=':', precision=1, alwayssign=True)}")
    elif len(a.pos) == 2:
        ra, dec = parse_coord(*a.pos)
    else:
        p.error("give either NAME, or RA DEC")
    scale = a.fov * 60.0 / a.npix                  # arcsec/pixel
    q = urllib.parse.urlencode(dict(ra=ra, dec=dec, scale=scale,
                                    width=a.npix, height=a.npix))
    with urllib.request.urlopen(f"{URL}?{q}", timeout=60) as r:
        img = Image.open(io.BytesIO(r.read()))

    # extent in arcmin offsets; RA increases to the left (East left)
    h = a.fov / 2
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(img, extent=[h, -h, -h, h], origin="upper")
    ax.add_patch(Circle((0, 0), a.diam / 2, fill=False, ec="cyan", lw=1.5))
    ax.plot(0, 0, "+", color="red", ms=10)
    ax.set_xlim(h, -h)
    ax.set_ylim(-h, h)
    ax.set_xlabel(r"$\Delta\alpha$ [arcmin]")
    ax.set_ylabel(r"$\Delta\delta$ [arcmin]")
    title = f"RA={ra:.5f}  DEC={dec:+.5f}   FOV={a.fov}'  circle D={a.diam}'"
    if a.name:
        title = f"{a.name}   " + title
    ax.set_title(title, fontsize=10)

    out = a.out or (f"{a.name}_sdss.png" if a.name else f"sdss_{ra:.4f}_{dec:+.4f}.png")
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
