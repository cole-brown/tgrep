#!/usr/bin/env python2.6
#

"""tgrep: grep HAproxy logs by timestamp, assuming logs are fully sorted

Sometimes two different sections of a log will match a supplied time range. For example, the log file goes from Feb
12 06:30 to Feb 13 07:00, and the user asks for logs with timestamp 6:50. That's in both the Feb 12 and Feb 13 parts
of the file. tgrep will find and print both.

Usage: tgrep times
   Or: tgrep times [file]
   Or: tgrep times [options] [file]
   Or: tgrep [options] times [file]
   Or: tgrep [options] [file] times
   ...I don't really care; do whatever you want. Just gimme my times.

Example:
   $ tgrep 8:42:04
     [log lines with that precise timestamp]
   $ tgrep 10:01
     [log lines with timestamps between 10:01:00 and 10:01:59]
   $ tgrep 23:59-0:03
     [log lines between 23:59:00 and 0:03:59]
   $ tgrep 23:59:30-0:03:01
     [log lines between 23:59:30 and 0:03:01]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -b, --binary          use pure binary search instead of time-adjusted binary
                        search
  -c CONFIG, --configfile=CONFIG
                        config file to use
  -e, --verbose-to-stderr
                        print statistics to stderr at end of run
  --ee                  print all statistics to stderr at end of run
  -v, --verbose         print statistics to stdout at end of run (-e
                        supercedes)
  --vv                  print all statistics to stdout at end of run (-e or
                        --ee supercedes)
"""

###
# Gentlemen, set your window width to 120 characters. You have been warned.
###

__author__     = "Cole Brown (spydez)"
__copyright__  = "Copyright 2011"
__credits__    = ["The reddit Backend Challenge (http://redd.it/fjgit)", "Cole Brown"]
__license__    = "BSD-3"
__version__    = "0.8.42" # //!
__maintainer__ = "Cole Brown"
__email__      = "git@spydez.com"
__status__     = "Development" # "Prototype", "Development", or "Production"


requirements = """
1. It has to give the right answer, even in all the special cases. (For extra credit, list all the special cases you can think of in your README)

2. It has to be fast. During testing, keep count of how many times you call lseek() or read(), and then make those numbers smaller. (For extra credit, give us the big-O analysis of the typical case and the worst case)

3. Elegant code is better than spaghetti.

By default it uses /logs/haproxy.log as the input file, but you can specify an alternate filename by appending it to the command line. It also works if you prepend it, because who has time to remember the order of arguments for every little dumb script?

The log file is usually about 60-70GB by the end of the day.
We usually get about 1500 log lines per second at peak and about 500 per second at the valley.

- When you're ready to submit your work, send a PM to #redditjobs and we'll tell you where to send your code. You can also write to that mailbox if you need clarification on anything.
- We'd like all the submissions to be in by Tuesday, February 22.
- Regardless of which project you pick, we ask you to please keep your work private until the end of March. After that, you can do whatever you want with it -- it's your code, after all!
"""

todo = """
Rename folder PertGyp

README.mk

grep //! 

Make sure it works on >4 GB files. Mostly the seek func. Python natively supports big ints.

turn off debug print

Classify the functions in here.
  LogSearch
    tgrep (time grep)
    bgrep (binary grep)
    attributes:
      log
      path_to_log
      times
      guesses
      filesize

turn off prints, debugs
remove "# DEBUG"

prettify the errors from NoMatch and parse_time (rethrow ValueError as something else)

README.
  Tested on raldi's generated log, my generated log, and a >4 GB file
  speed at cost of a few extra seek/reads
  Assumes flat/linear layout of log. No traffic bumps or dips.
  -v option
  expanded acceptable time inputs


Notes:
  http://gskinner.com/RegExr/    # REGEX!
  http://docs.python.org/library/multiprocessing.html
  http://docs.python.org/library/queue.html#Queue.Queue
  http://docs.python.org/library/os.html
  http://docs.python.org/release/2.4.4/lib/bltin-file-objects.html
  http://backyardbamboo.blogspot.com/2009/02/python-multiprocessing-vs-threading.html
  http://effbot.org/zone/wide-finder.htm#a-multi-threaded-python-solution
"""


# Python imports
import os
import sys
from datetime import datetime, timedelta
from optparse import OptionParser
import re
import imp
from copy import deepcopy

# local imports
import logloc
from logloc import LogLocation
from anomaly import NotFound, NotTime, RegexError
if __name__ != '__main__':
  # Auto-load for unit tests. Usually loaded down at bottom via imp.
  from config import stats, config

# CONSTANTS //! purge unused first, then move to config.py

DEFAULT_CONFIG = 'config.py'

# The only required arg is time
MIN_NUM_ARGS = 1
MAX_NUM_ARGS = 2 # time and file path

# //! constants than need moving somewhere else
LOOKING_FOR_MIN     = 0
LOOKING_FOR_MAX     = 1
LOOKING_FOR_BOTH    = 2
LOOKING_FOR_NEITHER = 3

#----------------------------------------------------------------------------------------------------------------------
# tgrep: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def tgrep(arg_time_str, path_to_log, search_type):
  """Searches the log file for entries in the range of the datetimes in the times list.

  Inputs:
    arg_time_str - validated to at least have a colon in it...
    path_to_log  - validated to be the path to an existing file.

  Returns: Nothing

  Raises:  Nothing

  Prints:  Logs
  """

  filesize = os.path.getsize(path_to_log)
  stats.file_size = pretty_size(filesize)

  end   = None
  start = datetime.now()
  # open 'rb' to avoid a bug in file.tell() in windows when file has unix line endings, even though I can't test in
  # windows, and have nyo idea if the rest will work there.
  # //! open and file-related funcs throw IOError. also catch stuff my funcs throw
  with open(path_to_log, 'rb') as log: 
    log_timestamps = [first_timestamp(log), last_timestamp(log)]
    DBG("first: %s" % log_timestamps[0]) # DEBUG
    DBG("last:  %s" % log_timestamps[1]) # DEBUG
    req_times = arg_time_parse(arg_time_str, log_timestamps[0])

    # DEBUG
    # //! only here temp. These are for loggen.log
    # Feb 13 23:33 (whole minute)
#    all_times = [[datetime(2011, 2, 13, 23, 33, 00), datetime(2011, 2, 13, 23, 34, 00)]]
    # Feb 13 23:33:11 (one log line)
#    all_times = [[datetime(2011, 2, 13, 23, 33, 11), datetime(2011, 2, 13, 23, 33, 11)]]
    # Feb 14 07:07:39 (End of File, exactly one line)
#    all_times = [[datetime(2011, 2, 14, 7, 7, 39), datetime(2011, 2, 14, 7, 7, 39)]]
    # Feb 14 07:07:39 (End of File, chunk)
#    all_times = [[datetime(2011, 2, 14, 7, 7, 0), datetime(2011, 2, 14, 7, 7, 39)]]
    # Feb 14 07:07:39 (End of File, chunk, no exact matches)
#    all_times = [[datetime(2011, 2, 14, 7, 7, 0), datetime(2011, 2, 14, 7, 9, 0)]]
    # Feb 13 18:31:30 (Start of File, exactly one line)
#    all_times = [[datetime(2011, 2, 13, 18, 31, 30), datetime(2011, 2, 13, 18, 31, 30)]]
    # Feb 13 18:31:30 (Start of File, chunk)
#    all_times = [[datetime(2011, 2, 13, 18, 31, 30), datetime(2011, 2, 13, 18, 32, 0)]]
    # Feb 13 18:30:30 (Start of File, chunk, no exact matches)
#    all_times = [[datetime(2011, 2, 13, 18, 30, 30), datetime(2011, 2, 13, 18, 32, 5)]]
    # NO MATCH!
#    all_times = [[datetime(2011, 2, 14, 1, 3, 0), datetime(2011, 2, 14, 1, 3, 0)]]
    # NO MATCH Feb 13 18:31:30 (before Start of File)
#    all_times = [[datetime(2011, 2, 13, 4, 31, 30), datetime(2011, 2, 13, 17, 31, 30)]]

    stats.requested_times = req_times
    DBG(req_times) # DEBUG

#    DBG("at: %s" % all_times) # DEBUG
    all_times = time_check(req_times, log_timestamps)
    DBG("at: %s" % all_times) # DEBUG
    for times in all_times:

      # Jump around the file in binary time-based fashion first
      DBG("\n\nwide sweep") # DEBUG
      sweep_start = datetime.now()
      hits, nearest_guesses = wide_sweep(log, filesize, times, search_type, log_timestamps)
      sweep_end = datetime.now()
      stats.wide_sweep_time = sweep_end - sweep_start
      stats.wide_sweep_end_locs.append(deepcopy(nearest_guesses))
  
      # Now that we're close, find the edges of the desired region of the log in linear fashion
      DBG("\n\nedge sweep") # DEBUG
      sweep_start = datetime.now()
      edge_sweep(log, hits, nearest_guesses, filesize, times) # updates nearest_guesses, so no return
      sweep_end = datetime.now()
      stats.edge_sweep_time = sweep_end - sweep_start
  
      # Figure out how much time searching took.
      end = datetime.now()
      DBG("\n\n") # DEBUG
      stats.find_time = end - start
  
      stats.final_locs.append(nearest_guesses)
      start = datetime.now()
      # Now, on to printing!
      # nearest_guesses is now a misnomer. They're the bounds of the region-to-print.
      print_log_lines(log, nearest_guesses)
  
      # Figure out how much time printing took.
      end = datetime.now()
      stats.print_time = end - start
      
      if len(all_times) > 1:
        print config.DOUBLE_MATCH_SEP


#----------------------------------------------------------------------------------------------------------------------
# time_check: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def time_check(times, log_timestamps):
  """Determines if times are valid for supplied log_timestamps.

  Since no day is supplied on the command line, there could be a double match in the file: one on the first day and one on the second. If so, this 

  Inputs:
    times       - Should be a list of size two with the low and high times requeted.
    log_timestamps  - [first timestamp in file, last timestamp in file]

  Returns: 
    list - a list of 'times' lists. Could be just [times]. Might be [times, [times[0]+a_day, times[1]+a_day]].

  Raises: Nothing
  """
  times_plus = [times[0].replace(day=times[0].day+1), times[1].replace(day=times[1].day+1)]
  all_times = [times, times_plus]
#  DBG("times: %s" % times     ) # DEBUG
#  DBG("+1day: %s" % times_plus) # DEBUG

  result = []
  for tlist in all_times:
    if (log_timestamps[0] <= tlist[0] <= log_timestamps[1]) or (log_timestamps[0] <= tlist[1] <= log_timestamps[1]):
      result.append(tlist)

#  DBG(result) # DEBUG
  return result
  


#----------------------------------------------------------------------------------------------------------------------
# wide_sweep: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def wide_sweep(log, filesize, times, search_type, log_timestamps):
  """Binary search of log file, with time-based adjustment, to get min/max guesses close to the range.

  Inputs:
    log            - opened log file
    filesize       - size of log
    times          - Should be a list of size two with the min and max datetimes. Format: [min, max]
    search_type    - True: use binary_search_guess; False: use time_search_guess
    log_timestamps - [first timestamp in file, last timestamp in file]

  Returns: 
    (LogLocation a, [LogLocation, LogLocation]) tuple
      a    - any exact matches from previous search methods
      list - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries

  Raises: Nothing
  """
  # binary search, with friends!
  search_func = None
  if search_type:
#    DBG("BINARY search!") # DEBUG
    search_func = binary_search_guess
  else:
#    DBG("TIME search!") # DEBUG
    search_func = time_search_guess

  # start min guess way too low, and max guess way too high. Just to prime the pump.
  too_high_time = log_timestamps[1].replace(second=log_timestamps[1].second + 1)
  nearest_guesses = [LogLocation(0,        log_timestamps[0],  LogLocation.TOO_LOW,  LogLocation.TOO_LOW),
                     LogLocation(filesize, too_high_time,      LogLocation.TOO_HIGH, LogLocation.TOO_HIGH)]
  focus = 0 # where we'll jump to for the text search
  hits  = [] # any exact matches to min or max we happen upon along the way
  done = False
  is_min_guess = False # toggle
  focus_adjustment = [1.0, 1.0] # no adjustment //! should not be using anymore
#  refocus = lambda f, m, f_adj: int((f - m) * f_adj + m) # //!
  bad_results = [0, 0]
  # binary time-based search until focal point comes up the same twice or we're close enough as per config param
  while not done:
    for time in times:
      is_min_guess = not is_min_guess # toggle 
      if bad_results[0 if is_min_guess else 1] > config.WIDE_SWEEP_MAX_RANGE_HITS:
        if bad_results[1 if is_min_guess else 0] > config.WIDE_SWEEP_MAX_RANGE_HITS: # note the 0 & 1 swap
          # If we've gotten both wrong too much, give up.
          done = True
          break
        # If we've gotten this guess wrong too much, just skip it.
        continue

      stats.wide_sweep_loops += 1
      if bad_results[0 if is_min_guess else 1]:
        stats.refocused_wide_sweep_loops += 1

      # time_search_guess, probably. Maybe binary_search_guess.
      focus = search_func(nearest_guesses, time, log_timestamps, filesize, is_min_guess)
      DBG("focus: %10d" % focus) # DEBUG
      DBG("f_adj: %7.3f" % focus_adjustment[0 if is_min_guess else 1]) # DEBUG
      if bad_results[0 if is_min_guess else 1]:
        focus = refocus(nearest_guesses, focus, is_min_guess)
#      focus = refocus(focus, nearest_guesses[0].get_loc(), focus_adjustment[0 if is_min_guess else 1]) # //!
      DBG("focus: %10d" % focus) # DEBUG
      DBG("binary: %d" % binary_search_guess(nearest_guesses, time, log_timestamps, filesize, is_min_guess)) # DEBUG
      DBG("time:   %d" % focus) # DEBUG

      try:
        if isinstance(focus, float):
          DBG("FOCUS IS FLOAT!!!") # DEBUG
        result = pessimistic_forward_search(log, focus, times, nearest_guesses, filesize) # check focus for timestamp
        good_result = update_guess(result, nearest_guesses) # updates nearest_guesses in place
      except ValueError:
        # something went wrong... dunno what, but we couldn't parse a timestamp from that location
        good_result = False
        # //! Real error? 

      if LogLocation.MATCH in result.get_minmax():
        DBG("found it!") # DEBUG
        hits.append(result)

      DBG(result) # DEBUG
      DBG(good_result) # DEBUG

      if not good_result and is_min_guess:
#        focus_adjustment[0] = config.WIDE_SWEEP_SLOW_FACTOR # //!!
        bad_results[0] += 1
      elif not good_result and not is_min_guess:
#        # We want to 'pull back' the next guess by a fator of WIDE_SWEEP_SLOW_FACTOR. So if slow-down is 25%, that means
#        # guess 25% of normal /back from end/. This involves two parts: 100% of start-to-focus, and 25% of
#        # end-to-focus. Or, to put a better way, 75% of focus-to-end.
#        # This means a 25% slow factor comes out to a 175% focus_adjustment.
#        focus_adjustment[1] = 1 + (1 - config.WIDE_SWEEP_SLOW_FACTOR) # //!!
        bad_results[1] += 1

#      DBG("bad low: %d" % bad_results[0] ) # DEBUG
#      DBG("bad high: %d" % bad_results[1]) # DEBUG
      DBG(nearest_guesses) # DEBUG
   
      # check if we can quit yet
      if (nearest_guesses[1].get_loc() - nearest_guesses[0].get_loc()) < config.WIDE_SWEEP_CLOSE_ENOUGH:
        # //! use expected_size here instead?
        DBG("close enough!") # DEBUG
        done = True # exit while
        break # exit for
      DBG("") # DEBUG
  
  DBG(hits) # DEBUG
  DBG(nearest_guesses) # DEBUG
  DBG((nearest_guesses[1].get_loc() - nearest_guesses[0].get_loc(), nearest_guesses[0].get_loc(), nearest_guesses[1].get_loc())) # DEBUG

  return hits, nearest_guesses

    
#----------------------------------------------------------------------------------------------------------------------
# edge_sweep: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def edge_sweep(log, hits, nearest_guesses, filesize, times):
  """Searches the log file up from the lower guess and down from the higher for the bounds of the desired log entries.

  Inputs:
    log             - opened log file
    hits            - any exact matches from previous search methods (LogLocation)
    nearest_guesses - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries
    filesize        - size of log
    times           - Should be a list of size two with the min and max datetimes. Format: [min, max]

  Updates in place:
    hits
    nearest_guesses

  Returns: Nothing

  Raises:  
    NotFound - desired range does not exist
  """
  # Find the extenses of the range. Range could still be fucking gigabytes!.. Which would take a while to print.

#  expected = expected_size(nearest_guesses[0].get_time(), nearest_guesses[1].get_time())
#  current  = nearest_guesses[1].get_loc() - nearest_guesses[0].get_loc()
#
#  if current > expected * config.EDGE_SWEEP_PESSIMISM_FACTOR: # //! move this to wide sweep
#    # Well, fuck. wide_sweep did a shitty job.
#    DBG("Well, fuck. wide_sweep did a shitty job.") # DEBUG
#    # //! implement!!! time/binary search inward from min/max
#    return
#//!
#  elif current =< config.EDGE_SWEEP_CHUNK_SIZE:
#    # mmap the whole thing, search like a banshee.
#    return

  # Now we do the edge finding the incremental way. We take our min & max from nearest_guesses, send them to
  # optimistic_edge_search to linearly search from that min/max, and process the result to get a better min/max guess or
  # the actual boundry of the desired log range.
  done = False
  looking_for = LOOKING_FOR_BOTH # We want both min and max boundries right now.
  while not done:
    for near_guess in nearest_guesses:
      if near_guess.get_is_boundry():
        continue # It's already been found. Continue to the other.
      stats.edge_sweep_loops += 1
      DBG("ng: %s" % near_guess) # DEBUG
      result = optimistic_edge_search(log, near_guess, looking_for, times, filesize)

      # //! need to check guess error state

      # DEBUG
      if config.DEBUG_PRINT:
        if result.get_minmax() == LogLocation.OUT_OF_RANGE_LOW:
          print "< ",  # DEBUG
        elif result.get_minmax() == LogLocation.OUT_OF_RANGE_HIGH:
          print "> ",  # DEBUG
        else:
          print "? ",  # DEBUG
        print result  # DEBUG

      update_guess(result, nearest_guesses) # updates nearest_guesses in place
      if result.get_is_min():
#        DBG("found min! %s" % result.get_time()) # DEBUG
        # Found the lower boundry. Switch to looking for upper or neither, depending.
        looking_for = LOOKING_FOR_MAX if looking_for == LOOKING_FOR_BOTH else LOOKING_FOR_NEITHER
      elif result.get_is_max():
#        DBG("found max! %s" % result.get_time()) # DEBUG
        # Found the upper boundry. Switch to looking for lower or neither, depending.
        looking_for = LOOKING_FOR_MIN if looking_for == LOOKING_FOR_BOTH else LOOKING_FOR_NEITHER

    DBG(nearest_guesses ) # DEBUG

    if looking_for == LOOKING_FOR_NEITHER:
      done = True
  
  # Should never be true unless someone fucks up optimistic_edge_search or update_guess.
  if not nearest_guesses[0].get_is_boundry() or not nearest_guesses[1].get_is_boundry():
    raise NotFound("Desired logs not found.", times, nearest_guesses)

  DBG(nearest_guesses) # DEBUG


#----------------------------------------------------------------------------------------------------------------------
# refocus
#----------------------------------------------------------------------------------------------------------------------
def refocus(nearest_guesses, focus, for_min):
  """Moves the search focal point away from the original focus.

  If searching right on the focus doesn't work, call this function to move the focus out towards the min or max.
  It will move it by config.

  Inputs:
    nearest_guesses - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries
    focus           - location in file intended to focus search
    for_min         - True if this guess should be for min, False otherwise

  Returns:
    int - refocused focal point

  Raises: Nothing
  """
  rf = 0
  if for_min:
    # focus - nearest_guesses[0] == distance into region
    # 1 - REFOCUS_FACTOR == percent into region desired to refocus to
    # add back nearest_guesses[0] to get refocused distance from beginning of file
    rf = (focus - nearest_guesses[0].get_loc()) * (1 - config.REFOCUS_FACTOR) + nearest_guesses[0].get_loc()
  else:
    rf = (nearest_guesses[1].get_loc() - focus) * config.REFOCUS_FACTOR + nearest_guesses[0].get_loc()

  DBG("rf: %7.3f" % rf) # DEBUG
  return int(rf)

#----------------------------------------------------------------------------------------------------------------------
# binary_search_guess
#----------------------------------------------------------------------------------------------------------------------
def binary_search_guess(nearest_guesses, desired, log_timestamps, filesize, for_min):
  """Straight up regular binary search calculation.

  Inputs:
    nearest_guesses - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries
    desired         - [IGNORED]
    log_timestamps  - [IGNORED]
    filesize        - [IGNORED]
    for_min         - [IGNORED]

  Returns:
    int - point in file to seek to next search

  Raises: Nothing
  """
  # ((max - min) / 2) to split the difference, then (that + min) to get in between min and max
  focus = ((nearest_guesses[1].get_loc() - nearest_guesses[0].get_loc()) / 2) + nearest_guesses[0].get_loc()
  return focus

#----------------------------------------------------------------------------------------------------------------------
# time_search_guess: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def time_search_guess(nearest_guesses, desired, log_timestamps, filesize, for_min):
  """Time-adjusted binary (TAB) search calculation. Considers times supplied as well. 

  Inputs:
    nearest_guesses - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries
    desired         - datetime we're looking for in the log
    log_timestamps  - [start, end] of the file in datetimes
    filesize        - size of log
    for_min         - True if this guess should be for min, False otherwise

  Returns:
    int - point in file to seek to next search

  Raises: Nothing
  """
  SECONDS_PER_DAY = 86400
  # For now, we assume last_timestamp() got called.
  #if nearest_guesses[1].get_time() == datetime.max:
  #  # haven't hit any actual point in the file, yet, so max guess is at default value.
  #  pass

  # Let's do a little math. Let:
  #  r = lowest  guess in nearest_guesses (datetime)
  #  e = highest guess in nearest_guesses (datetime)
  #  d = desired time (datetime)
  #  d = desired time (datetime)
  #  i = lowest  guess location in log file
  #  t = highest guess location in log file
  #
  # (x - y) is the time between two datetime objects (i.e. (r - e), (d - r) or (e - d)). Datetime math results in a
  # timedelta object, so we have to convert this to an integer.
  #  j = x - y (timedelta)
  #  o = j.days * SECONDS_PER_DAY
  #  b = o + j.seconds
  #
  # Let:
  #  p = b of (r - e) (start to end seconds)
  #  l = b of (d - r) (start to desired seconds)
  #  z = b of (e - d) (desired to end seconds)
  # 
  # Now, after calculating the number of seconds, we must find the percentage of the way through the region that d
  # is. We then use this time percentage to calculate the percentage in bytes with an assumption, quite simply, that
  # time % == bytes %. Add this 'bytes into the region' to i, and you get the estimated location of the time. <FIX WITH
  # MAX's BYTES PER SEC STUFF>
  #  K = (l / p)
  #  T = 1 - (z / p) 
  #  H = (K * (t-i)) + i (the answer for min)
  #  X = (K * (t-i)) + i + bytes_per_sec (the answer for max, one second worth of bytes above min's answer)

  low_j  = desired - nearest_guesses[0].get_time()
  high_j = nearest_guesses[1].get_time() - desired
  total_j  = nearest_guesses[1].get_time() - nearest_guesses[0].get_time()
#  DBG("    r: %s" % nearest_guesses[0].get_time()) # DEBUG
#  DBG("    d: %s" % desired) # DEBUG
#  DBG("    e: %s" % nearest_guesses[1].get_time()) # DEBUG
#  DBG("   lj: %s: %3d, %6d" % (low_j,  low_j.days,  low_j.seconds)) # DEBUG
#  DBG("   hj: %s: %3d, %6d" % (high_j, high_j.days, high_j.seconds)) # DEBUG
#  DBG("   tj: %s: %3d, %6d" % (total_j, total_j.days, total_j.seconds)) # DEBUG

  # If asked for a time before or after the file, the following would faithfully calculate how far away that is, so
  # here's a good place to stop and check our boundries.
  zero_td = timedelta(0)
  low_j  = zero_td if low_j  < zero_td else low_j
  high_j = zero_td if high_j < zero_td else high_j
  low_j  = total_j if low_j  > total_j else low_j
  high_j = total_j if high_j > total_j else high_j

  ob = lambda foo: foo.days * SECONDS_PER_DAY + foo.seconds

  BYTES_PER_SEC = filesize / float(ob(log_timestamps[1] - log_timestamps[0])) * config.BYTES_PER_SECOND_FUDGE_FACTOR
  DBG("   BPS: %6d" % BYTES_PER_SEC) # DEBUG

  p = ob(total_j)
  l = ob(low_j)
  z = ob(high_j)
#  DBG("     p: %6d" % p) # DEBUG
#  DBG("     l: %6d" % l) # DEBUG
#  DBG("     z: %6d" % z) # DEBUG

#  KTH = ((l / float(p)) + (1 - (z / float(p)))) / 2 # //! not used anymore
  K = l / float(p)
  DBG("     K: %7.3f" % (l / float(p))) # DEBUG
  DBG("     T: %7.3f" % (1 -  (z / float(p)))) # DEBUG
#  DBG(" %%KTH: %7.3f" % KTH) # DEBUG //! not used anymore

  H = (K * (nearest_guesses[1].get_loc() - nearest_guesses[0].get_loc())) + nearest_guesses[0].get_loc()
  X = (K * (nearest_guesses[1].get_loc() - nearest_guesses[0].get_loc())) + nearest_guesses[0].get_loc() + BYTES_PER_SEC
#  print "    X: %7.3f" % X

  
  return int(H) if for_min else int(X)

#----------------------------------------------------------------------------------------------------------------------
# first_timestamp: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def first_timestamp(log):
  """Reads the beginning of the file to find the first timestamp.

  Inputs:
    log - opened log file

  Returns:
    datetime - first timestamp in file

  Raises: 
    ValueError - parse_time had error parsing string into datetime
  """
  if log.tell() != 0:
    log.seek(0) # please please please don't make me seek...
  chunk = log.read(config.LOG_TIMESTAMP_SIZE) # Just need barely enough to get the whole timestamp from the first line.
#  DBG(chunk) # DEBUG
  stats.reads += 1

  # get the datetime
  return parse_time(chunk)

#----------------------------------------------------------------------------------------------------------------------
# last_timestamp
#----------------------------------------------------------------------------------------------------------------------
def last_timestamp(log):
  """Reads the end of the file to find the last timestamp.

  Inputs:
    log - opened log file

  Returns:
    datetime - last timestamp in file

  Raises: 
    ValueError - parse_time had error parsing string into datetime
  """
  log.seek(-config.MORE_THAN_ONE_LINE, os.SEEK_END) # minus sign is important
  chunk = log.read(config.MORE_THAN_ONE_LINE) # Just need barely enough to get the whole timestamp from the first line.

  nl_index = chunk[:-1].rfind("\n") # file could end with a newline so go back one in the chunk to skip it
  if nl_index == -1:
    return None
    # //! better error case? use rindex so it raises ValueError?
  nl_index += 1 # get past the newline

  stats.reads += 1

  # get the datetime
  return parse_time(chunk[nl_index : nl_index + config.LOG_TIMESTAMP_SIZE])

#----------------------------------------------------------------------------------------------------------------------
# pessimistic_forward_search
#----------------------------------------------------------------------------------------------------------------------
def pessimistic_forward_search(log, seek_loc, times, nearest_guesses, filesize):
  """Reads only a little and checks only the first timestamp after the first newline. 

  Inputs:
    log       - opened log file
    seek_loc  - location to seek to and read
    times     - Should be a list of size two with the min and max datetimes. Format: [min, max]
    nearest_guesses - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries
    fillesize -  size of log

  Returns:
    LogLocation - containing seek_loc, time parsed, and min/max comparision to min/max times in times list

  Raises: 
    ValueError - parse_time had error parsing string into datetime
  """
  log.seek(seek_loc)
  stats.seeks += 1

  # "More than one line" means it needs a newline and at least LOG_TIMESTAMP_SIZE bytes after that
  chunk = log.read(config.MORE_THAN_ONE_LINE) 
  stats.reads += 1
  at_eof = True if log.tell() == filesize else False # Python, why u no have file.eof?

  # find the nearest newline so we can find the timestamp
  nl_index = chunk.find("\n")
  if (nl_index == -1):
    if at_eof:
      return nearest_guesses[1]
    # else let parse throw. We got a corrupt file or something. //! handle better?
  nl_index += 1 # get past the newline

  # At end of file. Return max nearest_guess.
  if at_eof and chunk[nl_index:] == '':
    return nearest_guesses[1]

  # find the first bit of the line, e.g. "Feb 14 05:52:12 web0"
  # send to parse_time to get datetime
  time = parse_time(chunk[nl_index : nl_index + config.LOG_TIMESTAMP_SIZE])

  result = LogLocation(seek_loc + nl_index, time,
                       logloc.time_cmp(time, times[0]), # how it compares, min
                       logloc.time_cmp(time, times[1])) # how it compares, max
  return result

#----------------------------------------------------------------------------------------------------------------------
# optimistic_edge_search
#----------------------------------------------------------------------------------------------------------------------
def optimistic_edge_search(log, guess, looking_for, times, filesize):
  """Reads a large(r) chunk and checks it for the min or max boundry.

  Inputs:
    log         - opened log file
    guess       - A LogLocation to start from for finding an edge.
    looking_for - LOOKING_FOR_BOTH, LOOKING_FOR_MIN, or LOOKING_FOR_MAX
    filesize    - size of log

  Returns:
    LogLocation - better guess, or an actual boundry

  Raises: Nothing
  """

  # //! make look for both min and max, since it's reading a chunk...

  if looking_for == LOOKING_FOR_NEITHER:
    return None  # //! better error case. raise InvalidArgument("don't take looking_for:", NEITHER) or something

  # DEBUG
  if config.DEBUG_PRINT:
    if looking_for == LOOKING_FOR_NEITHER:
      print "LOOKING_FOR_NEITHER" # DEBUG
    if looking_for == LOOKING_FOR_BOTH:
      print "LOOKING_FOR_BOTH" # DEBUG
    if looking_for == LOOKING_FOR_MIN:
      print "LOOKING_FOR_MIN" # DEBUG
    if looking_for == LOOKING_FOR_MAX:
      print "LOOKING_FOR_MAX" # DEBUG

  seek_loc = guess.get_loc()
  if guess.get_minmax() == LogLocation.OUT_OF_RANGE_HIGH:
    # we're looking for the max and we're above it, so read from a chunk away up to here.
#    DBG("looking high") # DEBUG
#    DBG("%d %d" % (guess.get_loc(), guess.get_loc() - config.EDGE_SWEEP_CHUNK_SIZE)) # DEBUG
    seek_loc -= config.EDGE_SWEEP_CHUNK_SIZE
    seek_loc = 0 if seek_loc < 0 else seek_loc
    log.seek(seek_loc)
    stats.seeks += 1
  else:
    # we're looking for the min and we're below it, so read starting here.
    log.seek(seek_loc)
    stats.seeks += 1
  chunk = log.read(config.EDGE_SWEEP_CHUNK_SIZE)
  stats.reads += 1
  at_eof = True if log.tell() == filesize else False # Python, why u no have file.eof?

  prev_minmax = guess.get_minmax()
  result = LogLocation(0, datetime.min,
                       LogLocation.TOO_LOW,
                       LogLocation.TOO_HIGH) # an invalid result to start with
  chunk_loc = 0
  end_loc   = chunk.rfind('\n')
  nl_index  = chunk_loc # index into chunk[chunk_loc:] of the newline we're looking for current loop
  while chunk_loc < end_loc:
#    DBG("%d / %d" % (seek_loc + chunk_loc, seek_loc + end_loc)) # DEBUG
    try:
      # find the first bit of the line, e.g. "Feb 14 05:52:12 web0"
      # send to parse_time to get datetime
      time = parse_time(chunk[chunk_loc : chunk_loc + config.LOG_TIMESTAMP_SIZE])

      # start building result
      result.set_loc(seek_loc + chunk_loc)
      result.set_time(time)

      # compare to desired to see if it's a better max
      if time > times[1]:
        result.set_minmax(LogLocation.TOO_HIGH, LogLocation.TOO_HIGH)
      elif time == times[1]:
        # do nothing for now about this match, may optimize to save it off later.
        result.set_rel_to_max(LogLocation.MATCH)
      else: # time < times[1]
        result.set_rel_to_max(LogLocation.TOO_LOW)
 
      # compare to desired to see if it's a better min
      if time < times[0]:
        result.set_rel_to_min(LogLocation.TOO_LOW)
      elif time == times[0]:
        # do nothing for now about this match, may optimize to save it off later.
        result.set_rel_to_min(LogLocation.MATCH)
      else: # time > times[0]
        result.set_rel_to_min(LogLocation.TOO_HIGH)

      # We jumped entirely over the range in one line. There is no spoon.
      if (prev_minmax == LogLocation.OUT_OF_RANGE_LOW) and (result.get_minmax() == LogLocation.OUT_OF_RANGE_HIGH):
        raise NotFound("Desired logs not found.", times, guess)

#      DBG(result.get_minmax()) # DEBUG

      # see if the result's a min or max bondry
      if (looking_for == LOOKING_FOR_MIN) or (looking_for == LOOKING_FOR_BOTH):
        if (prev_minmax[0] == LogLocation.TOO_LOW) and (result.get_rel_to_min() != LogLocation.TOO_LOW):
          # We passed into our range via min. This is one.
          result.set_is_min(True)
          break
      elif (looking_for == LOOKING_FOR_MAX) or (looking_for == LOOKING_FOR_BOTH):
        # check to see if it's the edge
        if (prev_minmax[1] != LogLocation.TOO_HIGH) and (result.get_rel_to_max() == LogLocation.TOO_HIGH):
          # We passed out of range. This loc is where we want to /stop/ reading. Save it!
          result.set_is_max(True)
          break

      prev_minmax = result.get_minmax()
      # find the next newline so we can find the next timestamp
      nl_index = chunk[chunk_loc:].find('\n')
      if nl_index == -1:
#        DBG("can't find new line") # DEBUG
        break # Can't find a newline; we're done.
      chunk_loc += nl_index + 1 # +1 to get past newline char
    except ValueError: # not a time string found
#      DBG("time parse error") # DEBUG
      #//! copy pasted code. bleh
      # we're ok with occasional non-time string lines. Might start the read in the middle of a line, for example.
      # find the next newline so we can find the next timestamp

      # We errored, so find the next newline...
      # //! put this in a func? Python passes refs to strings, right?
      nl_index = chunk[chunk_loc:].find('\n')
      if nl_index == -1:
#        DBG("can't find new line") # DEBUG
        break # Can't find a newline; we're done.
      chunk_loc += nl_index + 1 # +1 to get past newline char
  
  # if we read to the end of our LOOKING_FOR_MAX chunk, and don't find the in range or match -> too high edge,
  # then the_guess max IS the boundry max.
  if not result.get_is_boundry() and (looking_for == LOOKING_FOR_MAX):
    result.set_loc(guess.get_loc())
    result.set_time(guess.get_time())
    result.set_minmax(guess.get_rel_to_min(), guess.get_rel_to_max())
    result.set_is_max(True)

  # if we read a chunk at the end of the file, searched through that, and didn't come up with a min or max,
  # set the max to eof.
  if not result.get_is_boundry() and at_eof and ((looking_for == LOOKING_FOR_MAX) or (looking_for == LOOKING_FOR_BOTH)):
    result.set_loc(seek_loc + len(chunk))
    result.set_time(time)
    result.set_minmax(logloc.time_cmp(time, times[0]), logloc.time_cmp(time, times[1]))
    result.set_is_max(True)

  # If we're only looking for the min, and we hit eof and didn't find it... Well, it's not there, man. Sorry.
  if not result.get_is_min() and at_eof and (looking_for == LOOKING_FOR_MIN):
    result.set_loc(seek_loc + len(chunk))
    result.set_time(time)
    result.set_minmax(logloc.time_cmp(time, times[0]), logloc.time_cmp(time, times[1]))
    result.set_is_min(True)

#  DBG(result) # DEBUG
  return result

#----------------------------------------------------------------------------------------------------------------------
# parse_time: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def parse_time(time_str):
  """Tries to parse string into a datetime object.

  Inputs:
    time_str - timestamp from log, formatted like: "Feb 13 18:31:36". Will ignore extra junk at end.

  Returns:
    datetime - datetime representation of time_str, set to the current year

  Raises:
    ValueError - error parsing string into datetime
  """
  # split the string on the whitespace, e.g. ["Feb", "14", "05:52:12", "web0"]
  # join the first three back together again with ' ' as the seperator
  # parse the thing!
  # //! need to research a better (faster?) way to do this
  just_timestamp = ' '.join(time_str.split()[:config.LOG_TIMESTAMP_PARTS])

  # parse with the illustrious strptime
  return datetime.strptime(just_timestamp + str(datetime.now().year), "%b %d %H:%M:%S%Y")

#----------------------------------------------------------------------------------------------------------------------
# update_guess: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def update_guess(guess, nearest_guesses):
  """Updates the nearest_guesses list based on the guess.

  Inputs:
    nearest_guesses - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries
    guess           - A LogLocation that may or may not be better than the current guesses.

  Updates in place:
    nearest_guesses

  Returns: 
    Boolean - True if nearest_guesses improved, otherwise False

  Raises:  Nothing
  """
  improved = False

  if guess.get_is_min() == True: # set to min 'guess' if it's the Real Actual min boundry
    nearest_guesses[0] = guess
    improved = True

  elif guess.get_is_max() == True: # set to max 'guess' if it's the Real Actual max boundry
    nearest_guesses[1] = guess
    improved = True

  elif guess.get_rel_to_min() == LogLocation.TOO_LOW: # not far enough
    # Compare with min, replace if bigger
    if guess.get_loc() > nearest_guesses[0].get_loc():
      nearest_guesses[0] = guess
      improved = True

  elif guess.get_rel_to_max() == LogLocation.TOO_HIGH: # too far
    # Compare with max, replace if smaller
    if guess.get_loc() < nearest_guesses[1].get_loc():
      nearest_guesses[1] = guess
      improved = True

  return improved

#----------------------------------------------------------------------------------------------------------------------
# expected_size: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def expected_size(min_time, max_time):
  """Calculates the expected size of a region in the log based on the supplied times and config params.

  Inputs:
    min_time - smaller datetime 
    max_time - bigger  datetime 

  Returns:
    int - expected number of bytes that amount of time would fill in the log assuming max load

  Raises:  Nothing
  """
  # //! Use me somewhere! :(
  time_range = max_time - min_time
  seconds = time_range.days * 86400 + time_range.seconds # We're ignoring microseconds.

  expected_bytes = config.APPROX_MAX_LOGS_PER_SEC * config.LOGS_PER_SEC_FUDGE_FACTOR * config.AVG_LOG_SIZE * seconds
  return int(expected_bytes)

#----------------------------------------------------------------------------------------------------------------------
# print_log_lines: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def print_log_lines(log, bounds, writable=sys.stdout):
  """Prints to stdout the range of the log indicated by bounds.

  Inputs:
    log      - opened log file
    bounds   - List in form [min, max] of the bounds of LogLocation entries
    writable - writable object to print output to

  Returns: Nothing

  Raises:  Nothing
  """
  start_loc = bounds[0].get_loc()
  log.seek(start_loc)
  stats.seeks += 1

  end_loc = bounds[1].get_loc()

  # Print out the logs in question in chunks, so that we don't use too much memory.
  curr = start_loc
  while curr < end_loc:
    # only print up to the end of our range
    chunk_size = 0
    if curr + config.MAX_PRINT_CHUNK_SIZE <= end_loc:
      chunk_size = config.MAX_PRINT_CHUNK_SIZE
    else:
      chunk_size = end_loc - curr

    chunk = log.read(chunk_size)
    stats.reads += 1
    stats.print_reads += 1
    curr += chunk_size
  
    writable.write(chunk) # NOT A DEBUG STATEMENT! LEAVE ME IN!!!
#    DBG((chunk_size, end_loc - start_loc)) # DEBUG
#    DBG((start_loc, curr, end_loc)) # DEBUG

#----------------------------------------------------------------------------------------------------------------------
# arg_time_parse: Parses time from command line args
#----------------------------------------------------------------------------------------------------------------------
def arg_time_parse(input, first_time):
  """Parses time from command line args

  For a specific time, "8:42:04", only that time will be used
  For a seconds-lacking time, "10:01", that entire minute will be used ("10:01:00" to "10:01:59")
  For a specific range, "1:2:3-14:15:16", that specific range will be used.
  For a seconds-lacking range end, "59" will be the seconds. 
    ("10:01:01-10:04" -> "10:01:01-10:04:59")
    ("10:01-10:04"    -> "10:01:00-10:04:59")

  Inputs:
    input      - arg from the command line that might be a time or time range
    first_time - datetime of first timestamp in the log file

  Returns: 
    list - [min time, max time] (if one specific time was requested, min and max will be the same)

  Raises:
    NotTime - The input was not a properly formatted time string.
    RegexError - The regex went wonky.
  """
  time_regex = re.compile(config.TIME_REGEX, re.IGNORECASE) 
  times = time_regex.findall(input) # returns [(group1, group2)] for my regex
  if times == []:
    # Raise the alarm! No regex match!
#    DBG("NO MATCH!") # DEBUG
    raise NotTime("This is not in the right format. No regex match.", input)
  elif 0 < times[0] < 3:
    # Something's wrong with the regex. Only supposed to get 1 or 2 matches.
#    DBG("REGEX BUG!") # DEBUG
    raise RegexBug("Something went wrong with the regex.", config.TIME_REGEX, input)
  retval = []
  lacking_secs = False
  for time in times[0]:
    if time == '':
      continue # they only passed in one time, not a range
    lacking_secs = False # when have 2 times, don't care if first lacks seconds
    arr  = time.split(':')
    #//! We'll have to roll back the day to whatever the log starts with, + 1 if it's "before" the log starts
    # (and thus actually the next day). Use timedelta to get around new year's and such.
    # No, wait. Use first_time. Then replace h:m:s, then roll back if needed.
    if len(arr) == 2: # no seconds
      arr.append(0)
      lacking_secs = True
    t = first_time.replace(hour=int(arr[0]), minute=int(arr[1]), second=int(arr[2]), microsecond=0)
    if t < first_time: 
      # log file spans ~24 hrs, but probably there's the midnight crossing in there somewhere, so a time of 3:00 could
      # be tomorrow at 3 AM. When we replaced the time, if it is actually a 'tomomrrow' date, it would put us beneath
      # today's date.
      t = t + timedelta(days=1)
    retval.append(t)
  
  # if only one time was specified, stick a second one in to round out the [min, max] list.
  if len(retval) == 1:
    retval.append(retval[0])

  # if no seconds were requested, they want a range of a minute, so append one with 59 secs
  if lacking_secs:
    retval[1] = retval[1].replace(second=int(59))

#  DBG(retval) # DEBUG
  return retval

#----------------------------------------------------------------------------------------------------------------------
# pretty_size: I'm so pretty~ Oh so pretty~
#----------------------------------------------------------------------------------------------------------------------
def pretty_size(num):
  """Returns a string of the input bytes, prettily formatted for human reading. E.g. 2048-> '2 KiB'"""
  for x in ['bytes','KiB','MiB','GiB','TiB', 'PiB', 'EiB', 'ZiB', 'YiB']:
    if num < 1024.0:
      return "%3.1f %s" % (num, x)
    num /= 1024.0

#----------------------------------------------------------------------------------------------------------------------
# Sometimes you just want to make the voices go away...
#----------------------------------------------------------------------------------------------------------------------
def DBG(printable):
  """No one likes bugs..."""
  if config.DEBUG_PRINT:
    print printable





usage = """\
Usage: %prog times
   Or: %prog times [file]
   Or: %prog times [options] [file]
   Or: %prog [options] times [file]
   Or: %prog [options] [file] times
   ...I don't really care; do whatever you want. Just gimme my times.

Example:
   $ %prog 8:42:04
     [log lines with that precise timestamp]
   $ %prog 10:01
     [log lines with timestamps between 10:01:00 and 10:01:59]
   $ %prog 23:59-0:03
     [log lines between 23:59:00 and 0:03:59]
   $ %prog 23:59:30-0:03:01
     [log lines between 23:59:30 and 0:03:01"""
#----------------------------------------------------------------------------------------------------------------------
#                                                    The Main Event
#----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  # Setup arg parser
  parser = OptionParser(usage = usage, version="%%prog %s" % __version__)
  parser.add_option("-b", "--binary",
                    action="store_true", dest="binary_search", default=False,
                    help="use pure binary search instead of time-adjusted binary search")
  parser.add_option("-c", "--configfile", 
                    metavar="CONFIG", help="config file to use")
  parser.add_option("-e", "--verbose-to-stderr",
                    action="store_true", dest="verbose_error", default=False,
                    help="print statistics to stderr at end of run")
  parser.add_option("--ee",
                    action="store_true", dest="super_verbose_error", default=False,
                    help="print all statistics to stderr at end of run")
  parser.add_option("-v", "--verbose",
                    action="store_true", dest="verbose", default=False,
                    help="print statistics to stdout at end of run (-e supercedes)")
  parser.add_option("--vv",
                    action="store_true", dest="super_verbose", default=False,
                    help="print all statistics to stdout at end of run (-e or --ee supercedes)")
  
  (options, args) = parser.parse_args()

  ###
  # Check options
  ###
  v_opts = [options.verbose, options.verbose_error, options.super_verbose, options.super_verbose_error]
  if v_opts.count(True) > 1:
    parser.error("options -v, -e, --vv, and --ee are mutually exclusive")

  ###
  # load config
  ###
  config_file = ''
  if isinstance(options.configfile, basestring):
    if os.path.isfile(options.configfile):
      config_file = options.configfile
    else:
      parser.error("Config file '%s' does not exist." % options.configfile)
  else:
    config_file = DEFAULT_CONFIG

    # Won't load over my fucking import up above //!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  try:
    tgrep_config = imp.load_source('tgrep_config', config_file)
    from tgrep_config import stats, config
  except ImportError:
    parser.error("Could not load config from '%s'" % config_file)

  ###
  # verify inputs
  ###
  if len(args) < MIN_NUM_ARGS:
    parser.error("Missing the required 'times' argument.")
    # exit stage right w/ help message and that string
  if len(args) > MAX_NUM_ARGS:
    parser.error("Too many args. Just need times and path to log file.")

  # Next, check for colons. At least one of them needs at least one colon. That's the time!
  possible = []
  for arg in args:
    if arg.find(':') != -1:
      possible.append(arg) # Probably a time. Could possibly be a file, though.
      # Seriously, why let a colon into your file names OS X?
  if possible == []:
    parser.error("One of the args needs to be a time or time range.")

  # check for the file
  existing = []
  if len(args) != MIN_NUM_ARGS:
    for arg in args:
      if os.path.isfile(arg):
        existing.append(arg)
    # whine if log file doesn't exists
    if existing == []:
      parser.error("Neither arg was an existing file. '%s' and '%s' do not exist." % (args[0], args[1]))
    elif len(existing) == len(args):
      # too many files!!!
      parser.error("Both files exist. Either '%s' or '%s' should be moved or renamed." % (args[0], args[1]))
  else:
    existing.append(config.DEFAULT_LOG) # No log supplied, so use default

  # I'm paranoid...
  the_log = ''
  if len(existing) > 1:
    parser.error("Too many log files. Pick one: %s." % args)
  else:
    the_log = existing[0]

  # whittle the time possibles down to not-files
  for p in possible:
    if p == the_log:
      possible.remove(the_log)

  the_time = ''
  if len(possible) != 1:
    if the_log.find(':') != -1:
      parser.error("No time specified. The time-like arg was an existing file: '%s'." % the_log)
    else:
      parser.error("No time specified. args %s boiled down to nothing." % args)
  else:
    the_time = possible[0]
  
  # We still don't know whether the the_time is an actual time (or time range), or if it's just "x:y:z" or
  # something. tgrep will figure that out.

  ###
  # tgrep actually starts here...
  ###
  tgrep(the_time, the_log, options.binary_search) # grep the file

  ###
  # print statistics
  ###
  writable = sys.stdout
  if options.verbose_error or options.super_verbose_error:
    writable = sys.stderr
  if options.verbose or options.verbose_error or options.super_verbose or options.super_verbose_error:
    print >>writable, "\n\n -- statistics --"
    print >>writable, "seeks: %8d" % stats.seeks
    print >>writable, "reads: %8d (total)" % stats.reads
    print >>writable, "reads: %8d (just for printing)" % stats.print_reads
    print >>writable, "wide sweep loops: %4d (TAB or binary search)" % stats.wide_sweep_loops
    print >>writable, "edge sweep loops: %4d (linear search)" % stats.edge_sweep_loops
    print >>writable, "wide sweep time:  %s" % str(stats.wide_sweep_time)
    print >>writable, "edge sweep time:  %s" % str(stats.edge_sweep_time)
    print >>writable, "find  time:       %s" % str(stats.find_time)
    print >>writable, "print time:       %s" % str(stats.print_time)
    print >>writable, "total time:       %s" % str(stats.find_time + stats.print_time)
    print >>writable, "log file size:    %s" % stats.file_size

  if options.super_verbose or options.super_verbose_error:
    print >>writable, "refocused wide sweep loops: %4d" % stats.refocused_wide_sweep_loops
    print >>writable, "wide sweep locs: "
    print >>writable, stats.wide_sweep_end_locs
    print >>writable, "final locs: "
    print >>writable, stats.final_locs
    print >>writable, "requested times: "
    print >>writable, "[%s, %s]" % (str(stats.requested_times[0]), str(stats.requested_times[1]))

