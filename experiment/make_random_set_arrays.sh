#!/bin/bash

if [ $# != 1 ]; then
    echo "Usage: $0 <target file name>"
    exit 1
fi

# Target file name
target=$1

# Directory where this script lives
mydir=`dirname $0`

ls -1 "$mydir"/random_sets_*.txt | xargs cat >> "$mydir"/random_sets_tmp.txt
cat "$mydir"/random_sets_tmp.txt | awk -f "$mydir"/random_sets2arrays.awk > $target
rm "$mydir"/random_sets_tmp.txt
