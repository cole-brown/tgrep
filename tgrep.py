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

check beginning/end of file matches

Comment shit.
PyDoc func comments.

try single child, multi-child, single thread

Make sure it works on >4 GB files. Mostly the seek func. Python natively supports big ints.

Use classes instead of arrays and shit? Which is faster?

option to turn on seek/read output

x results @ y bytes each in memory is z MB

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
    - out of order entries (challenge assured always in order)

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
from guess import Guess

# constants
MORE_THAN_ONE_LINE = 500 # bytes
MAX_MMAP_SIZE = 1 * 1024 * 1024 # 1 MB
SEEK_BYTES = 376*9000 + 50

DEFAULT_LOG = "loggen.log" # //! "/log/haproxy.log" 

# God Damn Global Variables, cursed to eternal shame
times_seeked = 0
times_read   = 0

def tgrep(path_to_log):
  # whine if log file doesn't exists
  if not os.path.isfile(path_to_log):
    print "file '%s' does not exist" % path_to_log
    return
  # //! better place to whine?

  filesize = os.path.getsize(path_to_log)

  # //! only here temp.
  # Feb 13 23:33 (whole minute)
  times = [datetime(2011, 2, 13, 23, 33, 00), datetime(2011, 2, 13, 23, 34, 00)]

  # for single vs multi, just bump guesses down to 1.
  num_children = 1
  with open(path_to_log, 'r') as log:
    wide_search(log, filesize, times, num_children)

    # if (min_loc + max_loc) > MAX_MMAP_SIZE:
    #   mmap whole thing
    # else:
    #   hungry_search # finds edges, keeps matches, mmaps blocks 
    
def wide_search(log, filesize, times, num_procs):
  # binary search, with friends!

  # for the global counters...
  global times_seeked
  global times_read
  arr = Array('i', [times_seeked, times_read])

  guess_results   = Queue()
  nearest_guesses = [Guess(0,        datetime(1999, 1, 1, 00, 00, 00),  Guess.TOO_LOW,  Guess.TOO_LOW),  # //! make y1k safe
                     Guess(filesize, datetime.now().replace(year=3000), Guess.TOO_HIGH, Guess.TOO_HIGH)] # //! make y3k safe
  nearest_guesses = [[0,        datetime(1999, 1, 1, 00, 00, 00), [-1, -1]], # //! make y1k safe
                     [filesize, datetime.now().replace(year=3000), [1, 1]]]  # //! make y3k safe
  prev_focus, seek_guesses = binary_search_guess(nearest_guesses[0][0], nearest_guesses[1][0], num_procs)
  hits  = []
  found = False
  while not found:
    children = []
    for seek_loc in seek_guesses:
      p = Process(target=pessismistic_search, args=(log, seek_loc, times, guess_results, arr))
      p.start()
      children.append(p)
    for child in children:
      child.join() # wait for all procs to finish before calculating next step
    while not guess_results.empty():
      guess = guess_results.get()
      if guess[2][0] == 0 or guess[2][1] == 0:
        print "found it!" # //!
        hits.append(guess)
        found = True
        break
#      print guess
      nearest_guesses = update_guess(guess, nearest_guesses)
#      print nearest_guesses
#      print seek_guesses
      focus, seek_guesses = binary_search_guess(nearest_guesses[0][0], nearest_guesses[1][0], num_procs)
#      print seek_guesses

      if focus == prev_focus:
        print "steady state!" # //!
        found = True
        break
      prev_focus = focus
      # check for zeros, go to opmistic_search?
  
  print hits
  print nearest_guesses
  times_seeked = arr[0]
  times_read   = arr[1]

  return hits, nearest_guesses

def binary_search_guess(min, max, num_guesses):
  # //! require odd number! num_guesses % 2 != 0
  # ((max - min) / 2) to split the difference, then (that + min) to get in between min and max
  focus = ((max - min) / 2) + min
  guesses = [focus]
  OFFSET = 0.1 # //! do smarter. No checking over 100% right now.
  curr_offset = OFFSET
  for i in range(1, num_guesses, 2): # skip 0 because we already added the focus
    guesses.append(int(focus*(1-curr_offset)))
    guesses.append(int(focus*(1+curr_offset)))
    curr_offset+=OFFSET
  return focus, guesses

def time_search_guess(nearest_guesses, desired, num_guesses):
  # //! require odd number! num_guesses % 2 != 0
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
  # nearest: [min_guess, max_guess]

  if guess[2][0] == -1: # not far enough
    # Compare with min, replace if bigger
    if guess[0] > nearest_guesses[0][0]:
      nearest_guesses[0][0:3] = guess

  if guess[2][1] == 1: # too far
    # Compare with max, replace if smaller
    if guess[0] < nearest_guesses[1][0]:
      nearest_guesses[1][0:3] = guess

  return nearest_guesses





if __name__ == '__main__':
  now = datetime.today() # today() instead of now() to lose TZ info
  now.replace(microsecond=0)
  # get min and max via min=now and replace()
#  min = datetime(2011, 2, 1, 13, 34, 43)
#  print time_cmp("Feb  9 14:34:43", min)

  tgrep(DEFAULT_LOG) # //! change this...

  # parse input
  # figure out which file to open
  # figure out the time range
  # don't care about arg order
  print "seeks: %8d" % times_seeked
  print "reads: %8d" % times_read
