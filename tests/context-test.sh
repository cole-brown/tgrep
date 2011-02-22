#!/bin/bash
#

# called '.log' to avoid getting added to git repo

echo -e "\n\nTGREP"
time ../tgrep -c ../config.py --ee ../biglog.log "$1-$2" > x-tmp-context-tgrep.log
echo -e "\n\nBORING GREP"
date
#nice time grep -C 1 " $1" ../biglog.log > x-tmp-context-grep.log
nice time grep -B 1 " $1" ../biglog.log > x-tmp-context-grep.log
nice time grep -A 1 " $2" ../biglog.log >> x-tmp-context-grep.log
echo -e "\n\nHead TGREP"
head -n 2 x-tmp-context-tgrep.log
echo -e "\n\nHead GREP"
head -n 3 x-tmp-context-grep.log
echo -e "\n\nTail TGREP"
tail -n 2 x-tmp-context-tgrep.log
echo -e "\n\nTail GREP"
tail -n 3 x-tmp-context-grep.log
echo -e "\n\nDIFF"
diff -au x-tmp-context-grep.log x-tmp-context-tgrep.log | tee x-tmp-context-diff.log
echo -e "\n\n"
ls -lh x-tmp-context-tgrep.log
ls -lh x-tmp-context-grep.log
ls -lh x-tmp-context-diff.log
echo -e "\n"
