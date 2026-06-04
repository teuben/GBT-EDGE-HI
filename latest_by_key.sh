#!/bin/bash
# Usage: ./latest_by_key.sh [inputfile]
# Reads from a file or stdin, keeps only the LAST occurrence of each line per key (first word).

INPUT="${1:-/dev/stdin}"

awk -F','  '
{
    key = $1
    if (!(key in lines)) {
        order[++count] = key   # record insertion order on first sight
    }
    lines[key] = $0            # always overwrite, so last one wins
}
END {
    for (i = 1; i <= count; i++) {
        print lines[order[i]]
    }
}
' "$INPUT"
