#!/usr/bin/env python2.6
#

"""tgrep: grep HAproxy logs by timestamp, assuming logs are fully sorted

Usage: 
  //!

"""

__authors__ =   ['reddit@spydez.com (Cole Brown (spydez))']

requirements = """
1. It has to give the right answer, even in all the special cases. (For extra credit, list all the special cases you can think of in your README)

2. It has to be fast. During testing, keep count of how many times you call lseek() or read(), and then make those numbers smaller. (For extra credit, give us the big-O analysis of the typical case and the worst case)

3. Elegant code is better than spaghetti.

By default it uses /logs/haproxy.log as the input file, but you can specify an alternate filename by appending it to the command line. It also works if you prepend it, because who has time to remember the order of arguments for every little dumb script?
"""

todo = """
grep //!

Make sure to verify input.

Comment shit.
PyDoc func comments.

try single child, multi-child, single thread

Make sure it works on >4 GB files. Mostly the seek func. Python natively supports big ints.

Use classes instead of arrays and shit? Which is faster?

option to turn on seek/read output

README.
  O(log2). Other analysis. Number of children. Speed.
  http://backyardbamboo.blogspot.com/2009/02/python-multiprocessing-vs-threading.html
  Tested on OS X 10.6.y in Python 2.6.z
  Tested on raldi's generated log, my generated log, and a >4 GB file
  speed at cost of a few extra seek/reads
  Assumes flat/linear layout of log. No traffic bumps or dips.
  edge cases:
    - handles leap years
    - handles leap seconds
    - big files
    - fragile on date format
    - datetime's millisecs or year - avoided
    - doesn't reimplement the wheel for crufty stuff, like time.

Notes:
  http://docs.python.org/library/multiprocessing.html
  http://docs.python.org/library/queue.html#Queue.Queue
  http://docs.python.org/library/os.html
  http://docs.python.org/release/2.4.4/lib/bltin-file-objects.html
"""

# Python imports
import os
from multiprocessing import Process, Queue, Array
from datetime import datetime

# local imports


# constants
MORE_THAN_ONE_LINE = 500 # bytes
SEEK_BYTES = 376*9000 + 50

DEFAULT_LOG = "loggen.log" # //! "/log/haproxy.log" 

# God Damn Global Variables, cursed to eternal shame
times_seeked = 0
times_read   = 0

def doShit2(path_to_log):
  # whine if log file doesn't exists
  if not os.path.isfile(path_to_log):
    print "file '%s' does not exist" % path_to_log
    return
  # //! better place to whine?

  # for the global counters...
  global times_seeked
  global times_read
  arr = Array('i', [times_seeked, times_read])

  filesize = os.path.getsize(path_to_log)

  # //! only here temp.
  # Feb 13 23:33 (whole minute)
  times = [datetime(2011, 2, 13, 23, 33, 30), datetime(2011, 2, 13, 23, 34, 00)]

  # for single vs multi, just bump guesses down to 1.
  # filesize/2+-x%
  seek_guesses    = [filesize/2]#[0,376*9000 + 50,376*5000 + 50,376*3000 + 50]
  guess_results   = Queue()
  nearest_guesses = [[0,        datetime(1999, 1, 1, 00, 00, 00)],  # //! make y1k safe
                     [filesize, datetime.now().replace(year=3000)]] # //! make y3k safe
  children = []
  with open(path_to_log, 'r') as log:
    for i in range(15):
      for seek_loc in seek_guesses:
        p = Process(target=pessismistic_search, args=(log, seek_loc, times, guess_results, arr))
        p.start()
        children.append(p)
      for child in children:
        child.join() # wait for all procs to finish before calculating next step
      while not guess_results.empty():
        guess = guess_results.get()
        if guess[2][0] == 0 or guess[2][1] == 0:
          print "found it!"
          times_seeked = arr[0]
          times_read   = arr[1]
          return
        print guess
        nearest_guesses = update_guess(guess, nearest_guesses)
#        print nearest_guesses
#        print seek_guesses
        seek_guesses = [binary_search_guess(nearest_guesses[0][0], nearest_guesses[1][0])]
        print seek_guesses
        # update seek_guesses, loop
        # check for zeros, go to opmistic_search?

  times_seeked = arr[0]
  times_read   = arr[1]
    
def binary_search_guess(min, max):
  # ((max - min) / 2) to split the difference, then (that + min) to get in between min and max
  return ((max - min) / 2) + min

def time_bimary_search_guess(nearest_guesses, desired):
  # //! implement!
  pass

# Reads only a little and checks only the first timestamp. Better when it's way off base.
def pessismistic_search(log, seek_loc, times, results, arr):
  log.seek(seek_loc)
  arr[0] += 1
  chunk = log.read(MORE_THAN_ONE_LINE)
  arr[1] += 1
  # find the nearest newline so we can find the timestamp
  nl_index = chunk.find("\n")
  if nl_index == -1:
    results.put([seek_loc, -1])
    return
    # //! better error case?
  nl_index += 1 # get past the newline

  # find the first bit of the line, e.g. "Feb 14 05:52:12 web0"
  # split it on the whitespace, e.g. ["Feb", "14", "05:52:12", "web0"]
  # join the first three back together again with ' ' as the seperator
  # parse the thing!
  # //! need to research a better (faster?) way to do this
  time = parse_time(' '.join(chunk[nl_index:nl_index+20].split()[:3]))

  cmp_results = [time_cmp(time, times[0]),
                 time_cmp(time, times[1])]

  results.put([seek_loc, time, cmp_results])

def parse_time(time_str):
  return datetime.strptime(time_str + str(datetime.now().year), "%b %d %H:%M:%S%Y")

def time_cmp(log_time, desired):
  # make these consts, use consts in update_guess
  if log_time > desired:
    return 1 # 1 means "KEEP GOING DUDE!"
  elif log_time == desired:
    return 0 # Aw, yeah. We're awesome.
  else:
    return -1 # Too far! Pull back!

def update_guess(guess, nearest_guesses):
  # guess:   [loc, datetime, [cmp_min, cmp_max]]
  # nearest: [[loc, datetime], [loc, datetime]]

  if guess[2][0] == -1: # not far enough
    # Compare with min, replace if bigger
    if guess[0] > nearest_guesses[0][0]:
      nearest_guesses[0][0:2] = guess[:2]

  if guess[2][1] == 1: # too far
    # Compare with max, replace if smaller
    if guess[0] < nearest_guesses[1][0]:
      nearest_guesses[1][0:2] = guess[:2]

  return nearest_guesses


#def doShit(path_to_log):
#  children = []
#
#  # whine if log file doesn't exists
#  if not os.path.isfile(path_to_log):
#    print "file '%s' does not exist" % path_to_log
#
#  # //! state assumptions
#  seek_guesses = [0,0,0]
#  seek_g2 = []
#
#  with open(path_to_log, 'r') as log: 
##    log.seek(SEEK_BYTES)
#    for seek_loc in seek_guesses:
#      pid = os.fork()
#      if pid is not 0: # this is the parent 
#        children.append(pid)
#      else: # these are the children
#        log.seek(0)
#        chunk = log.read(2)
##       chunk = log.read(MORE_THAN_ONE_LINE)
#        print chunk
#        chunk = log.read(2)
#        print chunk
#        # find next date, compare
#        seek_g2.append(42)
#        os._exit(0)
#  
#    for child in children:
#      os.waitpid(child, 0)
#


if __name__ == '__main__':
  now = datetime.today() # today() instead of now() to lose TZ info
  now.replace(microsecond=0)
  # get min and max via min=now and replace()
#  min = datetime(2011, 2, 1, 13, 34, 43)
#  print time_cmp("Feb  9 14:34:43", min)

  doShit2(DEFAULT_LOG) # //! change this...

  # parse input
  # figure out which file to open
  # figure out the time range
  # don't care about arg order
  print "seeks: %8d" % times_seeked
  print "reads: %8d" % times_read
