#!/bin/bash

#bump to ~20000
#MAX_LOGS=10

MAX_SEC_APART=5
MAX_SAME_LOG=30
INITIAL_TIMESTAMP=1234567890
END_TIMESTAMP=0
((END_TIMESTAMP=INITIAL_TIMESTAMP + 90000)) # one day, one hour later

# switch to BLAH_BLAH_BLAH when done testing
TEST_BLAH="[rest of log]"
BLAH_BLAH_BLAH="web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} \"POST /api/vote HTTP/1.1\""

logline() {
  for i in {1..$1}
  do
    date -r $2 | awk -v f=2 -v t=4 '{ for (i=f; i<=t;i++) printf("%s%s", $i,(i==t) ? " " : OFS) }'
    echo $BLAH_BLAH_BLAH
  done
}

rand() {
  python -c "import random; print random.randrange($1,$2);"
}


timestamp=$INITIAL_TIMESTAMP
#logline $timestamp #start @ initial timestamp
#for ((i = 0; i < $MAX_LOGS - 1; i++))
#do
#  ((timestamp = timestamp + `rand $MAX_SEC_APART`))
#  logline $timestamp
#done

while [ $timestamp -lt $END_TIMESTAMP ]; do
  logline `rand 1 $MAX_SAME_LOG` $timestamp
  ((timestamp = timestamp + `rand 0 $MAX_SEC_APART`))
done

#echo "Fix while loop so that some logs are repeated via randrepeoat() (which needs implementing)."