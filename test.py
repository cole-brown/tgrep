#!/usr/bin/env python2.6

#MORE_THAN_ONE_LINE = 500 # bytes
#SEEK_BYTES = 376*9000 + 50
#
##chunk = ""
##s = 376
##with open('loggen.log', 'r') as f:
##  f.seek(SEEK_BYTES)
##  for i in range(10000):
##    s = -376 if s is 376 else 376
##    f.seek(s, 1)
##    chunk = f.read(MORE_THAN_ONE_LINE)
#
#for i in range(10000):
#  with open('loggen.log', 'r') as f:
#    f.seek(SEEK_BYTES)
#    chunk = f.read(MORE_THAN_ONE_LINE)
#
#print chunk
#

import mmap
import os


MORE_THAN_ONE_LINE = 500 # bytes
SEEK_BYTES = 376*9000 + 50

#chunk = ""
#seek_remainder = SEEK_BYTES % mmap.PAGESIZE
#s = 376
#with open('loggen.log', 'r') as f:
#  map = mmap.mmap(f.fileno(), length=mmap.PAGESIZE*2, prot=mmap.PROT_READ, offset=SEEK_BYTES - seek_remainder)
#  map.seek(seek_remainder, os.SEEK_CUR)
#  for i in range(10000):
#    s = -376 if s is 376 else 376
#    map.seek(s, os.SEEK_CUR)
#    chunk = map.read(MORE_THAN_ONE_LINE)

chunk = ""
seek_remainder = SEEK_BYTES % mmap.PAGESIZE
s = 376
with open('loggen.log', 'r') as f:
  for i in range(10000):
    map = mmap.mmap(f.fileno(), length=mmap.PAGESIZE*2, prot=mmap.PROT_READ, offset=SEEK_BYTES - seek_remainder)
    map.seek(seek_remainder+376, os.SEEK_CUR)
    chunk = map.read(MORE_THAN_ONE_LINE)

print chunk

#map = mmap.mmap(-1, 19)
#map.write("Hello world!\nFuck.")
#
#pid = os.fork()
#
##if pid == 0: # In a child process
#map.seek(0)
#print map.readline()
#
#if pid != 0:
#    map.close()
