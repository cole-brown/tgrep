#!/bin/bash
#

# called '.log' to avoid getting added to git repo

echo -e "\n\nTGREP"
time ./tgrep -c config.py --ee $1 > x-tmp-diff-tgrep.log
echo -e "\n\nBORING GREP"
date
nice time grep " $1" biglog.log > x-tmp-diff-grep.log
echo -e "\n\nDIFF"
time diff -au x-tmp-diff-grep.log x-tmp-diff-tgrep.log > x-tmp-diff-diff.log
echo -e "\n\n"
ls -lh x-tmp-diff-tgrep.log
ls -lh x-tmp-diff-grep.log
ls -lh x-tmp-diff-diff.log
echo -e "\n"
