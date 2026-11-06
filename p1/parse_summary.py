#!/usr/bin/env python3
"""Summarize a dysh summary.log: keep the rows with one PROCSEQN, grouped by object.

Usage: parse_summary.py [-p PROCSEQN] [-s SEQ] [-v V] [-w W] [-r] [logfile]
"""
import argparse


def parse_log(filename):
    """Return the table rows of a summary log as a list of dicts of strings.

    Column names come from the header line, so the column order doesn't matter.
    Anything before the header, or not matching its width, is skipped.
    """
    rows = []
    names = None
    with open(filename) as f:
        for line in f:
            words = line.split()
            if words[:1] == ["SCAN"]:
                # "# IF" and friends are one column name, but two words
                names = line.replace("# ", "#").split()
            elif names and len(words) == len(names) and words[0].isdigit():
                rows.append(dict(zip(names, words)))
    return rows


def group_rows(rows):
    """Group rows into blocks of consecutive rows with the same OBJECT."""
    blocks = []
    for row in rows:
        if not blocks or blocks[-1][0]["OBJECT"] != row["OBJECT"]:
            blocks.append([])
        blocks[-1].append(row)
    return blocks


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("logfile", nargs="?", default="summary.log")
    parser.add_argument("-p", "--procseqn", default="1", help="PROCSEQN to keep [%(default)s]")
    parser.add_argument("-s", "--seq", type=int, default=1, help="value for the second column [%(default)s]")
    parser.add_argument("-v", type=int, default=200, help="value for the v column [%(default)s]")
    parser.add_argument("-w", type=int, default=600, help="value for the w column [%(default)s]")
    parser.add_argument("-r", "--rows", action="store_true", help="print every row, not the summary")
    args = parser.parse_args()

    # VELOCITY=0 are the calibrators
    rows = [row for row in parse_log(args.logfile)
            if row["PROCSEQN"] == args.procseqn and float(row["VELOCITY"]) != 0]

    if args.rows:
        print(f"{'SCAN':>5s}  {'OBJECT':<12s} {'PROCSEQN':>8s} {'VELOCITY':>9s}")
        for row in rows:
            print(f"{row['SCAN']:>5s}  {row['OBJECT']:<12s} {row['PROCSEQN']:>8s} {float(row['VELOCITY']):>9.0f}")
        return

    blocks = [(block[0], ",".join(row["SCAN"] for row in block)) for block in group_rows(rows)]
    width = max((len(scans) for _, scans in blocks), default=0)
    for first, scans in blocks:
        print(f"{first['OBJECT']:<12s} {args.seq:3d} {scans:<{width}s} {float(first['VELOCITY']):>9.0f} {args.v} {args.w}")


if __name__ == "__main__":
    main()
