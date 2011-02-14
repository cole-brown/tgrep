#!/usr/bin/env python2.6
#

"""tgrep: grep HAproxy logs by timestamp, assuming logs are fully sorted

//! describe algorithm a bit maybe...

Usage: 
  //!

"""

###
# Gentlemen, set your window width to 120 characters. You have been warned.
###

__author__     = "Cole Brown (spydez)"
__copyright__  = "Copyright 2011"
__credits__    = ["The reddit Backend Challenge (http://redd.it/fjgit)", "Cole Brown"]
__license__    = "BSD-3"
__version__    = "0.0.4" # //!
__maintainer__ = "Cole Brown"
__email__      = "git@spydez.com"
__status__     = "Prototype" # "Prototype", "Development", or "Production" //! development?


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
Rename folder FAST. Fucking Alacritous (Something) Tgrep. ...yeah. I'm not NASA.
Move scripts to /scripts

Move version string somewhere common. All header shit somewhere common?

README.mk

grep //!

Make sure to verify input.

Make sure it works on >4 GB files. Mostly the seek func. Python natively supports big ints.

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

option to turn on/off statistics printing

x results @ y bytes each in memory is z MB

compile vs uncompiled

Fucking "guess" is everywhere

Better config? Like... hierarchical? Dunno. tgrep_config.py as a name? "config" might clash...

turn off prints, debugs
remove "# DEBUG"

README.
  O(log2). Other analysis. Speed. "Hot" vs "cold" cache. Estimated speed on 70 GB file.
  Developed and tested on OS X 10.6.6 in Python 2.6.1
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
    - file read error
    - assumes filelines are < ~950 bytes
    - reading beginning and end of file
    - only one log entry (works)
    - very large log entry section (probably works)
    - no log entry (works)
    - file does not end with newline

Notes:
  http://docs.python.org/library/multiprocessing.html
  http://docs.python.org/library/queue.html#Queue.Queue
  http://docs.python.org/library/os.html
  http://docs.python.org/release/2.4.4/lib/bltin-file-objects.html
  http://backyardbamboo.blogspot.com/2009/02/python-multiprocessing-vs-threading.html
"""


# Python imports
import os
from datetime import datetime

# local imports
import logloc
from logloc import LogLocation
from anomaly import NotFound

# CONSTANTS //! purge unused first, then move to config.py

# Maximum size in bytes of mmap-able region.
MAX_MMAP_SIZE = 1 * 1024 * 1024 # 1 MB //! get page size in here

# Used to estimate where in the log file a particular timestamp is.
APPROX_LOG_SIZE = 500 # bytes //! use to calc MORE_THAN_ONE_LINE
APPROX_MAX_LOGS_PER_SEC = 5 # //!1500
LOGS_PER_SEC_FUDGE_FACTOR = 1.2

# Must be more than the max log line by the length of the timestamp. Used in initial binary time-based search for
# reading chunks of the file. Must be more than one line so it can find a newline and find the timestamp after it.
MORE_THAN_ONE_LINE = APPROX_LOG_SIZE * 3 # bytes

# The initial binary time-based search will quit once it's either this close (in bytes) or stabalized.
WIDE_SWEEP_CLOSE_ENOUGH = 2048 # bytes. //! bump this up 2k is small.

# Amount (in bytes) of the file that the edge-finding algorithm will read in at a time. Higher /might/ give better
# speed but will also use more memory.
EDGE_SWEEP_CHUNK_SIZE = 2048 # bytes //! bump this up! 2k is small...
EDGE_SWEEP_PESSIMISM_FACTOR = 3 # curr * this > expected? Then we act all sad.

# Amount (in bytes) of the file that will be read and printed at a time. Higher should give better speed but
# will use more meory.
MAX_PRINT_CHUNK_SIZE = 2048 # bytes //! bump this up 2k is small...

# The size of the timestamp in bytes. "Feb 13 18:31:36" is 15 bytes for ASCII. Bump this up if you're modifying
# this to work with unicode. You're allowed to go over without penalty (except file read time); don't go under.
LOG_TIMESTAMP_SIZE = 20 # bytes
LOG_TIMESTAMP_PARTS = 3 # "Feb", "13", "18:31:36"

# Path to log to default to if none is specified on the command line.
DEFAULT_LOG = "loggen.log" # //! "/log/haproxy.log" 


# //! constants than need moving somewhere else
LOOKING_FOR_MIN     = 0
LOOKING_FOR_MAX     = 1
LOOKING_FOR_BOTH    = 2
LOOKING_FOR_NEITHER = 3

# God Damn Global Variables, cursed to eternal shame
stats = {
  'seeks' : 0,
  'reads' : 0,
  'print_reads' : 0,
  'wide_sweep_loops' : 0,
  'edge_sweep_loops' : 0,
  'wide_sweep_time'  : None,
  'edge_sweep_time'  : None,
  'find_time'  : None,
  'print_time' : None
}


#----------------------------------------------------------------------------------------------------------------------
# tgrep: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def tgrep(times, path_to_log):
  """Searches the log file for entries in the range of the datetimes in the times list.

  Inputs:
    times       - Should be a list of size two with the min and max datetimes. Format: [min, max]
    path_to_log - The path to the log file.

  Returns: Nothing

  Raises:  Nothing
  """
  # verify inputs //!

  # whine if log file doesn't exists
  if not os.path.isfile(path_to_log):
    print "file '%s' does not exist" % path_to_log
    return
  # //! better place to whine?

  filesize = os.path.getsize(path_to_log)

  # DEBUG
  # //! only here temp. These are for loggen.log
  # Feb 13 23:33 (whole minute)
#  times = [datetime(2011, 2, 13, 23, 33, 00), datetime(2011, 2, 13, 23, 34, 00)]
  # Feb 13 23:33:11 (one log line)
  times = [datetime(2011, 2, 13, 23, 33, 11), datetime(2011, 2, 13, 23, 33, 11)]
  # NO MATCH!
#  times = [datetime(2011, 2, 14, 1, 3, 0), datetime(2011, 2, 14, 1, 3, 0)]
  # Feb 14 07:07:39 (End of File, exactly one line)
#  times = [datetime(2011, 2, 14, 7, 7, 39), datetime(2011, 2, 14, 7, 7, 39)]
  # Feb 14 07:07:39 (End of File, chunk)
#  times = [datetime(2011, 2, 14, 7, 7, 0), datetime(2011, 2, 14, 7, 7, 39)]
  # Feb 14 07:07:39 (End of File, chunk, no exact matches)
#  times = [datetime(2011, 2, 14, 7, 7, 0), datetime(2011, 2, 14, 7, 9, 0)]
  # Feb 13 18:31:30 (Start of File, exactly one line)
#  times = [datetime(2011, 2, 13, 18, 31, 30), datetime(2011, 2, 13, 18, 31, 30)]
  # Feb 13 18:31:30 (Start of File, chunk)
#  times = [datetime(2011, 2, 13, 18, 31, 30), datetime(2011, 2, 13, 18, 32, 0)]
  # Feb 13 18:31:30 (Start of File, chunk, no exact matches)
#  times = [datetime(2011, 2, 13, 18, 30, 30), datetime(2011, 2, 13, 18, 32, 5)]
  print "desired: %s" % str(times[0]) # DEBUG
  print "desired: %s" % str(times[1]) # DEBUG

  end   = None # DEBUG?
  start = datetime.now() # DEBUG?
  # open 'rb' to avoid a bug in file.tell() in windows when file has unix line endings, even though I can't test in
  # windows, and have nyo idea if the rest will work there.
  global stats
  with open(path_to_log, 'rb') as log: 
    print "first: %s" % str(first_timestamp(log)) # DEBUG

    # Jump around the file in binary time-based fashion first
    print "\n\nwide sweep" # DEBUG
    sweep_start = datetime.now() # DEBUG?
    hits, nearest_guesses = wide_sweep(log, filesize, times)
    sweep_end = datetime.now() # DEBUG?
    stats['wide_sweep_time'] = sweep_end - sweep_start # DEBUG?

    # Now that we're close, find the edges of the desired region of the log in linear fashion
    print "\n\nedge sweep" # DEBUG
    sweep_start = datetime.now() # DEBUG?
    edge_sweep(log, hits, nearest_guesses, filesize, times) # updates nearest_guesses, so no return
    sweep_end = datetime.now() # DEBUG?
    stats['edge_sweep_time'] = sweep_end - sweep_start # DEBUG?

    # Figure out how much time searching took.
    end = datetime.now() # DEBUG?
    print "\n\n" # DEBUG
    stats['find_time'] = end - start # DEBUG?

    start = datetime.now() # DEBUG?
    # if (min_loc + max_loc) > MAX_MMAP_SIZE:
    #   mmap whole thing
    # else:
    #   read()

    # Now, on to printing!
    # nearest_guesses is now a misnomer. They're the bounds of the region-to-print.
    print_log_lines(log, nearest_guesses)

    # Figure out how much time printing took.
    end = datetime.now() # DEBUG?
    stats['print_time'] = end - start # DEBUG?


#----------------------------------------------------------------------------------------------------------------------
# wide_sweep: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def wide_sweep(log, filesize, times):
  """Binary search of log file, with time-based adjustment, to get min/max guesses close to the range.

  Inputs:
    log             - opened log file
    filesize        - size of log
    times           - Should be a list of size two with the min and max datetimes. Format: [min, max]

  Returns: 
    (LogLocation, [LogLocation, LogLocation]) tuple
      LogLocation - any exact matches from previous search methods
      list        - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries

  Raises: Nothing
  """
  # binary search, with friends!

  # start min guess way too low, and max guess way too high. Just to prime the pump.
  nearest_guesses = [LogLocation(0,        datetime.min,  LogLocation.TOO_LOW,  LogLocation.TOO_LOW),
                     LogLocation(filesize, datetime.max, LogLocation.TOO_HIGH, LogLocation.TOO_HIGH)]
  focus = -1 # where we'll jump to for the text search
  hits  = [] # any exact matches to min or max we happen upon along the way
  done = False
  # binary time-based search until focal point comes up the same twice or we're close enough as per config param
  while not done:
    global stats
    stats['wide_sweep_loops'] += 1
    prev_focus = focus # which will be -1 the first time
    focus = binary_search_guess(nearest_guesses[0].get_loc(), 
                                nearest_guesses[1].get_loc())
    result = pessismistic_forward_search(log, focus, times) # check focus for timestamp
    # //! need to check error state
    if LogLocation.MATCH in result.get_minmax():
      print "found it!" # DEBUG
      hits.append(result)
#    print result # DEBUG
    update_guess(result, nearest_guesses) # updates nearest_guesses in place
#    print nearest_guesses # DEBUG
#    print seek_guesses # DEBUG
#    print seek_guesses # DEBUG

    # check if we can quit yet
    if focus == prev_focus:
      print "steady state!" # DEBUG
      done = True
    elif (nearest_guesses[1].get_loc() - nearest_guesses[0].get_loc()) < WIDE_SWEEP_CLOSE_ENOUGH:
      print "close enough!" # DEBUG
      done = True
  
  print hits # DEBUG
  print nearest_guesses # DEBUG
  print (nearest_guesses[1].get_loc() - nearest_guesses[0].get_loc(), nearest_guesses[0].get_loc(), nearest_guesses[1].get_loc()) # DEBUG

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
  # Find the extenses of the range. Range could still be fucking gigabytes!

  expected = expected_size(nearest_guesses[0].get_time(), nearest_guesses[1].get_time())
  current  = nearest_guesses[1].get_loc() - nearest_guesses[0].get_loc()

  if current > expected * EDGE_SWEEP_PESSIMISM_FACTOR: # //! move this to wide sweep
    # Well, fuck. wide_sweep did a shitty job.
    print "Well, fuck. wide_sweep did a shitty job." # DEBUG
    # //! implement!!! time/binary search inward from min/max
    return
#//!
#  elif current =< EDGE_SWEEP_CHUNK_SIZE:
#    # mmap the whole thing, search like a banshee.
#    return

  # Now we do the edge finding the incremental way. We take our min & max from nearest_guesses, send them to
  # optimistic_edge_search to linearly search from that min/max, and process the result to get a better min/max guess or
  # the actual boundry of the desired log range.
  done = False
  looking_for = LOOKING_FOR_BOTH # We want both min and max boundries right now.
  while not done:
    global stats
    stats['edge_sweep_loops'] += 1
    children = []
    for near_guess in nearest_guesses:
      if near_guess.get_is_boundry():
        continue # It's already been found. Continue to the other.
      print "ng: %s" % near_guess # DEBUG
      result = optimistic_edge_search(log, near_guess, looking_for, times, filesize)

      # //! need to check guess error state

      if result.get_minmax() == LogLocation.OUT_OF_RANGE_LOW:  # DEBUG
        print "< ",  # DEBUG
      elif result.get_minmax() == LogLocation.OUT_OF_RANGE_HIGH:  # DEBUG
        print "> ",  # DEBUG
      else:  # DEBUG
        print "? ",  # DEBUG
      print result  # DEBUG
      update_guess(result, nearest_guesses) # updates nearest_guesses in place
      if result.get_is_min():
#        print "found min! %s" % result.get_time() # DEBUG
        # Found the lower boundry. Switch to looking for upper or neither, depending.
        looking_for = LOOKING_FOR_MAX if looking_for == LOOKING_FOR_BOTH else LOOKING_FOR_NEITHER
      elif result.get_is_max():
#        print "found max! %s" % result.get_time() # DEBUG
        # Found the upper boundry. Switch to looking for lower or neither, depending.
        looking_for = LOOKING_FOR_MIN if looking_for == LOOKING_FOR_BOTH else LOOKING_FOR_NEITHER

    print nearest_guesses  # DEBUG

    if looking_for == LOOKING_FOR_NEITHER:
      done = True
  
  # Should never be true unless someone fucks up optimistic_edge_search or update_guess.
  if not nearest_guesses[0].get_is_boundry() or not nearest_guesses[1].get_is_boundry():
    raise NotFound("Desired logs not found.", times, nearest_guesses)

  print nearest_guesses # DEBUG


#----------------------------------------------------------------------------------------------------------------------
# binary_search_guess
#----------------------------------------------------------------------------------------------------------------------
def binary_search_guess(min, max):
  """Straight up regular binary search calculation.

  Inputs:
    min - low  seek location (int) to use in calculation
    max - high seek location (int) to use in calculation

  Returns:
    int - point in file to seek to next search

  Raises: Nothing
  """
  # ((max - min) / 2) to split the difference, then (that + min) to get in between min and max
  focus = ((max - min) / 2) + min
  return focus

#----------------------------------------------------------------------------------------------------------------------
# time_search_guess: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def time_search_guess(nearest_guesses, desired):
  """Modified binary search calculation. Considers times supplied as well.

  //! explain your algorithm, mister

  Inputs:
    nearest_guesses - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries
    desired         - datetime we're looking for in the log

  Returns:
    int - point in file to seek to next search

  Raises: Nothing
  """
  # //! implement!
  pass

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
  chunk = log.read(LOG_TIMESTAMP_SIZE) # Just need barely enough to get the whole timestamp from the first line.
#  print chunk # DEBUG
  global stats
  stats['reads'] += 1

  # get the datetime
  return parse_time(chunk)

#----------------------------------------------------------------------------------------------------------------------
# pessismistic_forward_search
#----------------------------------------------------------------------------------------------------------------------
def pessismistic_forward_search(log, seek_loc, times):
  """Reads only a little and checks only the first timestamp after the first newline. 

  Inputs:
    log      - opened log file
    seek_loc - location to seek to and read
    times    - Should be a list of size two with the min and max datetimes. Format: [min, max]

  Returns:
    LogLocation - containing seek_loc, time parsed, and min/max comparision to min/max times in times list

  Raises: 
    ValueError - parse_time had error parsing string into datetime
  """
  global stats
  log.seek(seek_loc)
  stats['seeks'] += 1

  # "More than one line" means it needs a newline and at least LOG_TIMESTAMP_SIZE bytes after that
  chunk = log.read(MORE_THAN_ONE_LINE) 
  stats['reads'] += 1

  # find the nearest newline so we can find the timestamp
  nl_index = chunk.find("\n")
  if nl_index == -1:
    return None
    # //! better error case?
  nl_index += 1 # get past the newline

  # find the first bit of the line, e.g. "Feb 14 05:52:12 web0"
  # send to parse_time to get datetime
  time = parse_time(chunk[nl_index : nl_index + LOG_TIMESTAMP_SIZE])

  result = LogLocation(seek_loc, time,                  # from before (no change)
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
  
  if looking_for == LOOKING_FOR_NEITHER: # DEBUG
    print "LOOKING_FOR_NEITHER" # DEBUG
  if looking_for == LOOKING_FOR_BOTH: # DEBUG
    print "LOOKING_FOR_BOTH" # DEBUG
  if looking_for == LOOKING_FOR_MIN: # DEBUG
    print "LOOKING_FOR_MIN" # DEBUG
  if looking_for == LOOKING_FOR_MAX: # DEBUG
    print "LOOKING_FOR_MAX" # DEBUG

  global stats
  seek_loc = guess.get_loc()
  if guess.get_minmax() == LogLocation.OUT_OF_RANGE_HIGH:
    # we're looking for the max and we're above it, so read from a chunk away up to here.
#    print "looking high" # DEBUG
#    print "%d %d" % (guess.get_loc(), guess.get_loc() - EDGE_SWEEP_CHUNK_SIZE) # DEBUG
    seek_loc -= EDGE_SWEEP_CHUNK_SIZE
    seek_loc = 0 if seek_loc < 0 else seek_loc
    log.seek(seek_loc)
    stats['seeks'] += 1
  else:
    # we're looking for the min and we're below it, so read starting here.
    log.seek(seek_loc)
    stats['seeks'] += 1
  chunk = log.read(EDGE_SWEEP_CHUNK_SIZE)
  stats['reads'] += 1
  at_eof = True if log.tell() == filesize else False # Python, why u no have file.eof?

  prev_minmax = guess.get_minmax()
  result = LogLocation(0, datetime.min,
                       LogLocation.TOO_LOW,
                       LogLocation.TOO_HIGH) # an invalid result to start with
  chunk_loc = 0
  end_loc   = chunk.rfind('\n')
  nl_index  = chunk_loc # index into chunk[chunk_loc:] of the newline we're looking for current loop
  while chunk_loc < end_loc:
#    print "%d / %d" % (seek_loc + chunk_loc, seek_loc + end_loc) # DEBUG
    try:
      # find the first bit of the line, e.g. "Feb 14 05:52:12 web0"
      # send to parse_time to get datetime
      time = parse_time(chunk[chunk_loc : chunk_loc + LOG_TIMESTAMP_SIZE])

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

#      print result.get_minmax() # DEBUG

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
#        print "can't find new line" # DEBUG
        break # Can't find a newline; we're done.
      chunk_loc += nl_index + 1 # +1 to get past newline char
    except ValueError: # not a time string found
#      print "time parse error" # DEBUG
      #//! copy pasted code. bleh
      # we're ok with occasional non-time string lines. Might start the read in the middle of a line, for example.
      # find the next newline so we can find the next timestamp

      # We errored, so find the next newline...
      # //! put this in a func? Python passes refs to strings, right?
      nl_index = chunk[chunk_loc:].find('\n')
      if nl_index == -1:
#        print "can't find new line" # DEBUG
        break # Can't find a newline; we're done.
      chunk_loc += nl_index + 1 # +1 to get past newline char
  
  # if we read a chunk at the end of the file, searched through that, and didn't come up with a min or max,
  # set the max to eof
  if not result.get_is_boundry() and at_eof and ((looking_for == LOOKING_FOR_MAX) or (looking_for == LOOKING_FOR_BOTH)):
    result.set_loc(seek_loc + len(chunk))
    result.set_time(times[1])
    result.set_minmax(LogLocation.TOO_HIGH, LogLocation.TOO_HIGH)
    result.set_is_max(True)
#  print "short circuit: %s" % time # DEBUG

#  print result # DEBUG
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
  just_timestamp = ' '.join(time_str.split()[:LOG_TIMESTAMP_PARTS])

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

  Returns: Nothing

  Raises:  Nothing
  """

  if guess.get_is_min() == True: # set to min 'guess' if it's the Real Actual min boundry
    nearest_guesses[0] = guess

  elif guess.get_is_max() == True: # set to max 'guess' if it's the Real Actual max boundry
    nearest_guesses[1] = guess

  elif guess.get_rel_to_min() == LogLocation.TOO_LOW: # not far enough
    # Compare with min, replace if bigger
    if guess.get_loc() > nearest_guesses[0].get_loc():
      nearest_guesses[0] = guess

  elif guess.get_rel_to_max() == LogLocation.TOO_HIGH: # too far
    # Compare with max, replace if smaller
    if guess.get_loc() < nearest_guesses[1].get_loc():
      nearest_guesses[1] = guess


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
  seconds = time_range.days * 3600 * 24 + time_range.seconds # We're ignoring microseconds.

  expected_bytes = APPROX_MAX_LOGS_PER_SEC * LOGS_PER_SEC_FUDGE_FACTOR * APPROX_LOG_SIZE * seconds
  return int(expected_bytes)

#----------------------------------------------------------------------------------------------------------------------
# print_log_lines: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
#----------------------------------------------------------------------------------------------------------------------
def print_log_lines(log, bounds):
  """Prints to stdout the range of the log indicated by bounds.

  Inputs:
    log    - opened log file
    bounds - List in form [min, max] of the bounds of LogLocation entries

  Returns: Nothing

  Raises:  Nothing
  """
  global stats

  start_loc = bounds[0].get_loc()
  log.seek(start_loc)
  stats['seeks'] += 1

  end_loc = bounds[1].get_loc()

  # Print out the logs in question in chunks, so that we don't use too much memory.
  curr = start_loc
  while curr < end_loc:
    # only print up to the end of our range
    chunk_size = 0
    if curr + MAX_PRINT_CHUNK_SIZE <= end_loc:
      chunk_size = MAX_PRINT_CHUNK_SIZE
    else:
      chunk_size = end_loc - curr

    chunk = log.read(chunk_size)
    stats['reads'] += 1
    curr += chunk_size
  
    stats['print_reads'] += 1
    print chunk # NOT A DEBUG STATEMENT! LEAVE ME IN!!!
    print (chunk_size, end_loc - start_loc) # DEBUG
    print (start_loc, curr, end_loc) # DEBUg



#----------------------------------------------------------------------------------------------------------------------
#                                                    The Main Event
#----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  # parse input
  # figure out which file to open
  # figure out the time range
  # don't care about arg order

  # grep the file
  tgrep([None, None], DEFAULT_LOG) # //! change this...

  # print statistics
  print "\n\n -- statistics --"
  print "seeks: %8d" % stats['seeks']
  print "reads: %8d" % stats['reads']
  print "print reads: %2d" % stats['print_reads']
  print "wide sweep loops: %3d" % stats['wide_sweep_loops']
  print "edge sweep loops: %3d" % stats['edge_sweep_loops']
  print "wide sweep time:  %s" % str(stats['wide_sweep_time'])
  print "edge sweep time:  %s" % str(stats['edge_sweep_time'])
  print "find  time:       %s" % str(stats['find_time'])
  print "print time:       %s" % str(stats['print_time'])
  print "total time:       %s" % str(stats['find_time'] + stats['print_time'])
