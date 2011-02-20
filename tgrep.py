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


todo = """
comment code
space out code?
  - [X] tgrep
  - [ ] logloc
  - [ ] anomaly
  - [ ] config-big
  - [ ] extra

backport updates to config-big

tgrep.py -> tgrep

remove bad guesses const from config.

make branch, remove debugs

remove header from logloc?

comment other files?
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
from anomaly import NotFound, NotTime, RegexError, InvalidArgument
if __name__ != '__main__':
  # Auto-load for unit tests. Usually loaded down at bottom via imp.
  from config import stats, config

# CONSTANTS
DEFAULT_CONFIG = 'config.py'

# The only required arg is time
MIN_NUM_ARGS = 1
MAX_NUM_ARGS = 2 # time and file path



#======================================================================================================================
# LogSearch: class containing that awesome tgrep function
#======================================================================================================================
class LogSearch:

  # used by edge sweep and optimistic search
  LOOKING_FOR_MIN     = 0
  LOOKING_FOR_MAX     = 1
  LOOKING_FOR_BOTH    = 2
  LOOKING_FOR_NEITHER = 3

  #--------------------------------------------------------------------------------------------------------------------
  # initialize them variables and such
  #--------------------------------------------------------------------------------------------------------------------
  def __init__(self, arg_time_str, path_to_log):
    """Initializes LogSearch.

    Inputs:
      input_time - validated to at least have a colon in it...
      log_path   - validated to be the path to an existing file.

    Returns: Nothing
  
    Raises:  Nothing
    """
    DBG("__init__") # DEBUG

    self.input_time = arg_time_str
    self.log_path   = path_to_log

  #--------------------------------------------------------------------------------------------------------------------
  # tgrep: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
  #--------------------------------------------------------------------------------------------------------------------
  def tgrep(self, search_type):
    """Searches the log file for entries in the range of the datetimes passed in to the constructor..
  
    Inputs:
  
    Returns: Nothing
  
    Raises:  Nothing
  
    Prints:  Logs
    """
    self.filesize   = os.path.getsize(self.log_path)
    stats.file_size = pretty_size(self.filesize)
  
    try:
      end   = None
      start = datetime.now()
      # open 'rb' to avoid a bug in file.tell() in windows when file has unix line endings, even though I can't test in
      # windows, and have no idea if the rest will work there.
      with open(self.log_path, 'rb') as self.log: 
        self.log_timestamps = [self.first_timestamp(), self.last_timestamp()]
        DBG("first: %s" % self.log_timestamps[0]) # DEBUG
        DBG("last:  %s" % self.log_timestamps[1]) # DEBUG
     
        # DEBUG - These are for loggen.log
        # Feb 13 23:33 (whole minute)
  #      all_times = [[datetime(2011, 2, 13, 23, 33, 00), datetime(2011, 2, 13, 23, 34, 00)]]
        # Feb 13 23:33:11 (one log line)
  #      all_times = [[datetime(2011, 2, 13, 23, 33, 11), datetime(2011, 2, 13, 23, 33, 11)]]
        # Feb 14 07:07:39 (End of File, exactly one line)
  #      all_times = [[datetime(2011, 2, 14, 7, 7, 39), datetime(2011, 2, 14, 7, 7, 39)]]
        # Feb 14 07:07:39 (End of File, chunk)
  #      all_times = [[datetime(2011, 2, 14, 7, 7, 0), datetime(2011, 2, 14, 7, 7, 39)]]
        # Feb 14 07:07:39 (End of File, chunk, no exact matches)
  #      all_times = [[datetime(2011, 2, 14, 7, 7, 0), datetime(2011, 2, 14, 7, 9, 0)]]
        # Feb 13 18:31:30 (Start of File, exactly one line)
  #      all_times = [[datetime(2011, 2, 13, 18, 31, 30), datetime(2011, 2, 13, 18, 31, 30)]]
        # Feb 13 18:31:30 (Start of File, chunk)
  #      all_times = [[datetime(2011, 2, 13, 18, 31, 30), datetime(2011, 2, 13, 18, 32, 0)]]
        # Feb 13 18:30:30 (Start of File, chunk, no exact matches)
  #      all_times = [[datetime(2011, 2, 13, 18, 30, 30), datetime(2011, 2, 13, 18, 32, 5)]]
        # NO MATCH!
  #      all_times = [[datetime(2011, 2, 14, 1, 3, 0), datetime(2011, 2, 14, 1, 3, 0)]]
        # NO MATCH Feb 13 18:31:30 (before Start of File)
  #      all_times = [[datetime(2011, 2, 13, 4, 31, 30), datetime(2011, 2, 13, 17, 31, 30)]]
     
        requested_times = self.input_time_parse(self.input_time, self.log_timestamps[0])
        stats.requested_times = requested_times
        DBG(requested_times) # DEBUG
     
  #      DBG("at: %s" % all_times) # DEBUG
        # check times, get two ranges if twice in log file
        all_times = self.time_check(requested_times)
        DBG("at: %s" % all_times) # DEBUG

        if all_times == []:
          print >>sys.stderr, "No matches for requested time in file."
          print >>sys.stderr, "input:            %s"   % str(self.input_time)
          print >>sys.stderr, "file start:       %s"   % str(self.log_timestamps[0])
          print >>sys.stderr, "file end:         %s\n" % str(self.log_timestamps[1])
          return
  
        # main tgrep loop
        for times in all_times:
     
          # Jump around the file in binary time-based fashion first
          DBG("\n\nwide sweep") # DEBUG
          sweep_start = datetime.now()
          self.hits, self.boundaries = self.wide_sweep(times, search_type)
          sweep_end = datetime.now()
          stats.wide_sweep_time = sweep_end - sweep_start
          stats.wide_sweep_end_locs.append(deepcopy(self.boundaries))
      
          # Now that we're close, find the edges of the desired region of the log in linear fashion
          DBG("\n\nedge sweep") # DEBUG
          sweep_start = datetime.now()
          self.edge_sweep(times) # updates self.boundaries, so no return
          sweep_end = datetime.now()
          stats.edge_sweep_time = sweep_end - sweep_start

          # self.boundaries is now the bounds of the region-to-print, not the bounds of the search.
      
          # Figure out how much time searching took.
          end = datetime.now()
          DBG("\n\n") # DEBUG
          stats.find_time = end - start
      
          stats.final_locs.append(self.boundaries)

          # Now, on to printing!
          start = datetime.now()
          self.print_log_lines()
      
          # Figure out how much time printing took.
          end = datetime.now()
          stats.print_time = end - start
          
          if (len(all_times) > 1) and (config.DOUBLE_MATCH_SEP != ''):
            print config.DOUBLE_MATCH_SEP
  
    # Beautify some errors, but keep it debug friendly.
    except NotTime as err:
      print >>sys.stderr, "Timestamp parser had a bit of trouble...\n"
      print >>sys.stderr, err
  
      if config.DEBUG:
        print "\n"
        raise
    except NotFound as err:
      print >>sys.stderr, "No match for '%s' time range in log file.\n" % self.input_time
      print >>sys.stderr, err
  
      if config.DEBUG:
        print "\n"
        raise
    except RegexError as err:
      print >>sys.stderr, "Regex trouble. The regex for parsing input time got an unexpected number of matches.\n"
      print >>sys.stderr, err
  
      if config.DEBUG:
        print "\n"
        raise
    except IOError as err:
      print >>sys.stderr, "Trouble reading or opening file.\n"
      print >>sys.stderr, err
  
      if config.DEBUG:
        print "\n"
        raise

  #--------------------------------------------------------------------------------------------------------------------
  # time_check: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
  #--------------------------------------------------------------------------------------------------------------------
  def time_check(self, times):
    """Determines if times are valid for supplied self.log_timestamps.
  
    Since no day is supplied on the command line, there could be a double match in the file: one on the first day and
    one on the second. If so, this will return both.
  
    Inputs:
      times - Should be a list of size two with the low and high times requeted.
  
    Returns: 
      list - a list of 'times' lists. Could be just [times]. Might be [times, [times[0]+a_day, times[1]+a_day]].
  
    Raises: Nothing
    """
    times_plus = [times[0].replace(day=times[0].day+1), times[1].replace(day=times[1].day+1)]
    all_times = [times, times_plus]
    DBG("times: %s" % times     ) # DEBUG
    DBG("+1day: %s" % times_plus) # DEBUG
    DBG(" file: %s" % self.log_timestamps)
  
    result = []
    for tlist in all_times:
      if (self.log_timestamps[0] <= tlist[0] <= self.log_timestamps[1]) or \
           (self.log_timestamps[0] <= tlist[1] <= self.log_timestamps[1]):
        result.append(tlist)
  
    DBG(result) # DEBUG
    return result
    
  #--------------------------------------------------------------------------------------------------------------------
  # wide_sweep: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
  #--------------------------------------------------------------------------------------------------------------------
  def wide_sweep(self, times, search_type):
    """Binary search of log file, with time-based adjustment, to get min/max guesses close to the range.
  
    Inputs:
      times          - Should be a list of size two with the min and max datetimes. Format: [min, max]
      search_type    - True: use binary_search_guess; False: use time_search_guess
  
    Returns: 
      (LogLocation a, [LogLocation, LogLocation]) tuple
        a    - any exact matches from previous search methods
        list - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries
  
    Raises: Nothing
    """
    # TAB search! Or... that boring binary fellow.
    search_func = None
    if search_type:
  #    DBG("BINARY search!") # DEBUG
      search_func = self.binary_search_guess
    else:
  #    DBG("TIME search!") # DEBUG
      search_func = self.time_search_guess
  
    # start min guess way too low, and max guess way too high. Just to prime the pump.
    too_high_time = self.log_timestamps[1].replace(second=self.log_timestamps[1].second + 1)
    self.boundaries = [LogLocation(0,             self.log_timestamps[0], LogLocation.TOO_LOW,  LogLocation.TOO_LOW),
                       LogLocation(self.filesize, too_high_time,          LogLocation.TOO_HIGH, LogLocation.TOO_HIGH)]

    focus = 0 # where we'll jump to for the text search
    hits  = [] # any exact matches to min or max we happen upon along the way
    done = False
    is_min_guess = False # toggle
    bad_results = [0, 0]
    # quickly search through file to get min/max guess as close as possible.
    while not done:
      for time in times: # requested region
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
        focus = search_func(time, is_min_guess)
        DBG("focus: %10d" % focus) # DEBUG
        if bad_results[0 if is_min_guess else 1]:
          focus = self.refocus(focus, is_min_guess)
        DBG("focus: %10d" % focus) # DEBUG
        DBG("binary: %d" % self.binary_search_guess(time, is_min_guess)) # DEBUG
        DBG("time:   %d" % focus) # DEBUG
  
        try:
          # check focus for timestamp
          result = self.pessimistic_forward_search(focus, times) 
          good_result = self.update_guess(result) # updates self.boundaries in place
        except NotTime:
          # something went wrong... dunno what, but we couldn't parse a timestamp from that location.
          good_result = False
  
        if LogLocation.MATCH in result.get_minmax():
          DBG("found it!") # DEBUG
          hits.append(result)
  
        DBG(result) # DEBUG
        DBG(good_result) # DEBUG
  
        if not good_result and is_min_guess:
          bad_results[0] += 1
        elif not good_result and not is_min_guess:
          bad_results[1] += 1
  
  #      DBG("bad low: %d" % bad_results[0] ) # DEBUG
  #      DBG("bad high: %d" % bad_results[1]) # DEBUG
        DBG(self.boundaries) # DEBUG
     
        # check if we can quit yet
        if (self.boundaries[1].get_loc() - self.boundaries[0].get_loc()) < config.WIDE_SWEEP_CLOSE_ENOUGH:
          DBG("close enough!") # DEBUG
          done = True # exit while
          break # exit for
        DBG("") # DEBUG
    
    DBG(hits) # DEBUG
    DBG(self.boundaries) # DEBUG
    DBG((self.boundaries[1].get_loc() - self.boundaries[0].get_loc(), 
         self.boundaries[0].get_loc(), self.boundaries[1].get_loc())) # DEBUG
  
    return hits, self.boundaries
  
  #--------------------------------------------------------------------------------------------------------------------
  # edge_sweep: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
  #--------------------------------------------------------------------------------------------------------------------
  def edge_sweep(self, times):
    """Searches the log file up from the lower guess and down from the higher for the bounds of the desired log entries.
  
    Inputs:
      times           - Should be a list of size two with the min and max datetimes. Format: [min, max]
  
    Updates in place:
      self.hits       - any exact matches from previous search methods (LogLocation)
      self.boundaries - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries
  
    Returns: Nothing
  
    Raises:  
      NotFound - desired range does not exist
    """
    # Find the extenses of the range. Range could still be fucking gigabytes! Which would take a while to print... But
    # still... don't assume anything.
  
    # Now we do the edge finding the incremental way. We take our min & max from self.boundaries, send them to
    # optimistic_edge_search to linearly search from that min/max, and process the result to get a better min/max guess
    # or the actual boundry of the desired log range.
    done = False
    looking_for = self.LOOKING_FOR_BOTH # We want both min and max boundries right now.
    while not done:
      for guess in self.boundaries:
        if guess.get_is_boundry():
          continue # It's already been found. Continue to the other.
        stats.edge_sweep_loops += 1
  
        DBG("guess: %s" % guess) # DEBUG
        # look for it...
        result = self.optimistic_edge_search(guess, looking_for, times)
  
        # DEBUG
        if config.DEBUG:
          if result.get_minmax() == LogLocation.OUT_OF_RANGE_LOW:
            print "< ",  # DEBUG
          elif result.get_minmax() == LogLocation.OUT_OF_RANGE_HIGH:
            print "> ",  # DEBUG
          else:
            print "? ",  # DEBUG
          print result  # DEBUG
  
        self.update_guess(result) # updates self.boundaries in place
        if result.get_is_min():
  #        DBG("found min! %s" % result.get_time()) # DEBUG
          # Found the lower boundry. Switch to looking for upper or neither, depending.
          looking_for = self.LOOKING_FOR_MAX if looking_for == self.LOOKING_FOR_BOTH else self.LOOKING_FOR_NEITHER
        elif result.get_is_max():
  #        DBG("found max! %s" % result.get_time()) # DEBUG
          # Found the upper boundry. Switch to looking for lower or neither, depending.
          looking_for = self.LOOKING_FOR_MIN if looking_for == self.LOOKING_FOR_BOTH else self.LOOKING_FOR_NEITHER
  
      DBG(self.boundaries) # DEBUG
  
      if looking_for == self.LOOKING_FOR_NEITHER:
        done = True
    
    # Should never be true unless someone fucks up optimistic_edge_search or update_guess. optimistic_edge_search itself
    # will raise NotFound for actual NotFound events.
    if not self.boundaries[0].get_is_boundry() or not self.boundaries[1].get_is_boundry():
      DBG("NOT FOUND!!!!") # DEBUG
      raise NotFound("Desired logs not found.", times, self.boundaries)
  
    DBG(self.boundaries) # DEBUG
  
  #--------------------------------------------------------------------------------------------------------------------
  # refocus
  #--------------------------------------------------------------------------------------------------------------------
  def refocus(self, focus, for_min):
    """Moves the search focal point away from the original focus.
  
    If searching right on the focus doesn't work, call this function to move the focus out towards the min or max.
    It will move it by config.
  
    Inputs:
      focus   - location in file intended to focus search
      for_min - True if this guess should be for min, False otherwise
  
    Returns:
      int - refocused focal point
  
    Raises: Nothing
    """
    rf = 0
    if for_min:
      # focus - self.boundaries[0] == distance into region
      # 1 - REFOCUS_FACTOR == percent into region desired to refocus to
      # add back self.boundaries[0] to get refocused distance from beginning of file
      rf = (focus - self.boundaries[0].get_loc()) * (1 - config.REFOCUS_FACTOR) + self.boundaries[0].get_loc()
    else:
      DBG("high:   %d %f" % (self.boundaries[1].get_loc(), self.boundaries[1].get_loc())) # DEBUG
      DBG("focus:  %d %f" % (focus, focus)) # DEBUG
      DBG("low:    %d %f" % (self.boundaries[0].get_loc(), self.boundaries[0].get_loc())) # DEBUG
      DBG("factor: %d %f" % (config.REFOCUS_FACTOR, config.REFOCUS_FACTOR)) # DEBUG
      rf = (self.boundaries[1].get_loc() - focus) * config.REFOCUS_FACTOR + self.boundaries[0].get_loc()
  
    DBG("rf: %7.3f" % rf) # DEBUG
    return int(rf)
  
  #--------------------------------------------------------------------------------------------------------------------
  # binary_search_guess
  #--------------------------------------------------------------------------------------------------------------------
  def binary_search_guess(self, desired, for_min):
    """Straight up regular binary search calculation.

    Must maintain input parity with other *_search_guess functions.
  
    Inputs:
      desired - [IGNORED]
      for_min - [IGNORED]
  
    Returns:
      int - point in file to seek to next search
  
    Raises: Nothing
    """
    # ((max - min) / 2) to split the difference, then (that + min) to get in between min and max
    focus = ((self.boundaries[1].get_loc() - self.boundaries[0].get_loc()) / 2) + self.boundaries[0].get_loc()
    return focus
  
  #--------------------------------------------------------------------------------------------------------------------
  # time_search_guess
  #--------------------------------------------------------------------------------------------------------------------
  def time_search_guess(self, desired, for_min):
    """Time-adjusted binary (TAB) search calculation. Considers times supplied as well. 
  
    Must maintain input parity with other *_search_guess functions.
  
    Inputs:
      desired         - datetime we're looking for in the log
      for_min         - True if this guess should be for min, False otherwise
  
    Returns:
      int - point in file to seek to next search
  
    Raises: Nothing
    """
    SECONDS_PER_DAY = 86400
    # Let's do a little math. Let:
    #  r = lowest  guess in self.boundaries (datetime)
    #  e = highest guess in self.boundaries (datetime)
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
    # time % == bytes %. Add this 'bytes into the region' to i, and you get the estimated min location of the time. For
    # the estimated max answer, you must also add the estimated bytes per second.
    #  K = (l / p)
    #  T = 1 - (z / p) 
    #  H = (K * (t-i)) + i (the answer for min)
    #  X = (K * (t-i)) + i + bytes_per_sec (the answer for max, one second worth of bytes above min's answer)
    # 
    # There is one catch for adding the estimated bytes per second to X: don't do it if it would put you over 
    # the max boundary.
  
    low_j  = desired - self.boundaries[0].get_time()
    high_j = self.boundaries[1].get_time() - desired
    total_j  = self.boundaries[1].get_time() - self.boundaries[0].get_time()
  #  DBG("    r: %s" % self.boundaries[0].get_time()) # DEBUG
  #  DBG("    d: %s" % desired) # DEBUG
  #  DBG("    e: %s" % self.boundaries[1].get_time()) # DEBUG
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
  
    BYTES_PER_SEC = self.filesize / float(ob(self.log_timestamps[1] - self.log_timestamps[0])) * \
        config.BYTES_PER_SECOND_FUDGE_FACTOR
    DBG("   BPS: %6d" % BYTES_PER_SEC) # DEBUG
  
    p = ob(total_j)
    l = ob(low_j)
    z = ob(high_j)
  #  DBG("     p: %6d" % p) # DEBUG
  #  DBG("     l: %6d" % l) # DEBUG
  #  DBG("     z: %6d" % z) # DEBUG
  
    K = l / float(p)
    DBG("     K: %7.3f" % (l / float(p))) # DEBUG
    DBG("     T: %7.3f" % (1 -  (z / float(p)))) # DEBUG
  
    H = (K * (self.boundaries[1].get_loc() - self.boundaries[0].get_loc())) + self.boundaries[0].get_loc()
    X = (K * (self.boundaries[1].get_loc() - self.boundaries[0].get_loc())) + \
        self.boundaries[0].get_loc() + BYTES_PER_SEC
    if X > self.boundaries[1].get_loc():
      # Whoops. Too far. Get rid of our "rest of the second's worth of bytes" estimate.
      X -= BYTES_PER_SEC
  
    # DEBUG
    if config.DEBUG:
      if for_min:
        DBG("   *H: %7.3f" % H) # DEBUG
        DBG("    X: %7.3f" % X) # DEBUG
      else:
        DBG("    H: %7.3f" % H) # DEBUG
        DBG("   *X: %7.3f" % X) # DEBUG
    
    return int(H) if for_min else int(X)
  
  #--------------------------------------------------------------------------------------------------------------------
  # first_timestamp: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
  #--------------------------------------------------------------------------------------------------------------------
  def first_timestamp(self):
    """Reads the beginning of the file to find the first timestamp.
  
    Inputs: None
  
    Returns:
      datetime - first timestamp in file
  
    Raises: 
      NotTime - parse_time had error parsing string into datetime
    """
    if self.log.tell() != 0:
      self.log.seek(0) # please please please don't make me seek...

    # Just need barely enough to get the whole timestamp from the first line.
    chunk = self.log.read(config.LOG_TIMESTAMP_SIZE)
  #  DBG(chunk) # DEBUG
    stats.reads += 1
  
    # get the datetime
    return self.parse_time(chunk)
  
  #--------------------------------------------------------------------------------------------------------------------
  # last_timestamp
  #--------------------------------------------------------------------------------------------------------------------
  def last_timestamp(self):
    """Reads the end of the file to find the last timestamp.
  
    Inputs: None
  
    Returns:
      datetime - last timestamp in file
  
    Raises: 
      NotTime - parse_time had error parsing string into datetime
    """
    self.log.seek(-config.MORE_THAN_ONE_LINE, os.SEEK_END) # Minus sign is important. Going back from end.
    stats.seeks += 1
    chunk = self.log.read(config.MORE_THAN_ONE_LINE) 
    stats.reads += 1
  
    nl_index = chunk[:-1].rfind("\n") # file could end with a newline so go back one in the chunk to skip it
    if nl_index == -1:
      raise NotTime("Could not find a timestamp at end of log file.", chunk)
    nl_index += 1 # get past the newline
  
    # get the datetime
    return self.parse_time(chunk[nl_index : nl_index + config.LOG_TIMESTAMP_SIZE])
  
  #--------------------------------------------------------------------------------------------------------------------
  # pessimistic_forward_search
  #--------------------------------------------------------------------------------------------------------------------
  def pessimistic_forward_search(self, seek_loc, times):
    """Reads only a little and checks only the first timestamp after the first newline. 
  
    Inputs:
      seek_loc  - location to seek to and read
      times     - Should be a list of size two with the min and max datetimes. Format: [min, max]
  
    Returns:
      LogLocation - containing seek_loc, time parsed, and min/max comparision to min/max times in times list
  
    Raises: 
      NotTime - parse_time had error parsing string into datetime
    """
    print "seek_loc: %d %f" % (seek_loc, seek_loc)
    self.log.seek(seek_loc)
    stats.seeks += 1
  
    # "More than one line" means it needs a newline and at least LOG_TIMESTAMP_SIZE bytes after that
    chunk = self.log.read(config.MORE_THAN_ONE_LINE) 
    stats.reads += 1
    at_eof = True if self.log.tell() == self.filesize else False # Python, why u no have file.eof?
  
    # find the nearest newline so we can find the timestamp
    nl_index = chunk.find("\n")
    if (nl_index == -1):
      if at_eof:
        return self.boundaries[1]
    nl_index += 1 # get past the newline
  
    # At end of file. Return max nearest_guess.
    if at_eof and chunk[nl_index:] == '':
      return self.boundaries[1]
  
    # find the first bit of the line, e.g. "Feb 14 05:52:12 web0"
    # send to parse_time to get datetime
    time = self.parse_time(chunk[nl_index : nl_index + config.LOG_TIMESTAMP_SIZE])
  
    result = LogLocation(seek_loc + nl_index, time,
                         logloc.time_cmp(time, times[0]), # how it compares, min
                         logloc.time_cmp(time, times[1])) # how it compares, max
    return result
  
  #--------------------------------------------------------------------------------------------------------------------
  # optimistic_edge_search
  #--------------------------------------------------------------------------------------------------------------------
  def optimistic_edge_search(self, guess, looking_for, times):
    """Reads a large(r) chunk and checks it for the min or max boundry.
  
    Inputs:
      guess       - A LogLocation to start from for finding an edge.
      looking_for - self.LOOKING_FOR_BOTH, self.LOOKING_FOR_MIN, or self.LOOKING_FOR_MAX
  
    Returns:
      LogLocation - better guess, or an actual boundry
  
    Raises: 
      InvalidArgument - self.LOOKING_FOR_NEITHER was passed in
    """
    if looking_for == self.LOOKING_FOR_NEITHER:
      raise InvalidArgument("LOOKING_FOR_NEITHER is not accepted", self.LOOKING_FOR_NEITHER)
  
    # DEBUG
    if config.DEBUG:
      if looking_for == self.LOOKING_FOR_NEITHER:
        print "LOOKING_FOR_NEITHER" # DEBUG
      if looking_for == self.LOOKING_FOR_BOTH:
        print "LOOKING_FOR_BOTH" # DEBUG
      if looking_for == self.LOOKING_FOR_MIN:
        print "LOOKING_FOR_MIN" # DEBUG
      if looking_for == self.LOOKING_FOR_MAX:
        print "LOOKING_FOR_MAX" # DEBUG
  
    seek_loc = guess.get_loc()
    if guess.get_minmax() == LogLocation.OUT_OF_RANGE_HIGH:
      # we're looking for the max and we're above it, so read from a chunk away up to here.
      DBG("looking high") # DEBUG
      DBG("%d %d" % (guess.get_loc(), guess.get_loc() - config.EDGE_SWEEP_CHUNK_SIZE)) # DEBUG
      seek_loc -= config.EDGE_SWEEP_CHUNK_SIZE
      seek_loc = 0 if seek_loc < 0 else seek_loc
      self.log.seek(seek_loc)
      stats.seeks += 1
    else:
      # we're looking for the min and we're below it, so read starting here.
      self.log.seek(seek_loc)
      stats.seeks += 1
    chunk = self.log.read(config.EDGE_SWEEP_CHUNK_SIZE)
    stats.reads += 1
    stats.edge_sweep_size += config.EDGE_SWEEP_CHUNK_SIZE
    at_eof = True if self.log.tell() == self.filesize else False # Python, why u no have file.eof?
  
    prev_minmax = guess.get_minmax()
    result = LogLocation(0, datetime.min,
                         LogLocation.TOO_LOW,
                         LogLocation.TOO_HIGH) # an invalid result to start with
    chunk_loc = 0
    end_loc   = chunk.rfind('\n')
    nl_index  = chunk_loc # index into chunk[chunk_loc:] of the newline we're looking for current loop

    # search linearly through the chunk
    while chunk_loc < end_loc:
      DBG("%d / %d" % (seek_loc + chunk_loc, seek_loc + end_loc)) # DEBUG
      try:
        # find the first bit of the line, e.g. "Feb 14 05:52:12 web0"
        # send to parse_time to get datetime
        time = self.parse_time(chunk[chunk_loc : chunk_loc + config.LOG_TIMESTAMP_SIZE])
        DBG(time) # DEBUG
        DBG(times) # DEBUG
  
        # start building result
        result.set_loc(seek_loc + chunk_loc)
        result.set_time(time)
  
        # compare to desired to see if it's a better max
        if time > times[1]:
          DBG("time > max") # DEBUG
          result.set_minmax(LogLocation.TOO_HIGH, LogLocation.TOO_HIGH)
        elif time == times[1]:
          DBG("time == max") # DEBUG
          # do nothing for now about this match, may optimize to save it off later.
          result.set_rel_to_max(LogLocation.MATCH)
        else: # time < times[1]
          DBG("time < max") # DEBUG
          result.set_rel_to_max(LogLocation.TOO_LOW)
   
        # compare to desired to see if it's a better min
        if time < times[0]:
          DBG("time < min") # DEBUG
          result.set_rel_to_min(LogLocation.TOO_LOW)
        elif time == times[0]:
          DBG("time == min") # DEBUG
          # do nothing for now about this match, may optimize to save it off later.
          result.set_rel_to_min(LogLocation.MATCH)
        else: # time > times[0]
          DBG("time > min") # DEBUG
          result.set_rel_to_min(LogLocation.TOO_HIGH)
  
        if (prev_minmax == LogLocation.OUT_OF_RANGE_LOW) and (result.get_minmax() == LogLocation.OUT_OF_RANGE_HIGH):
          # We jumped entirely over the range in one line. There is no spoon.
          raise NotFound("Desired logs not found.", times, guess)
  
  #      DBG(result.get_minmax()) # DEBUG
  
        # see if the result's a min or max bondry
        if (looking_for == self.LOOKING_FOR_MIN) or (looking_for == self.LOOKING_FOR_BOTH):
          if (prev_minmax[0] == LogLocation.TOO_LOW) and (result.get_rel_to_min() != LogLocation.TOO_LOW):
            # We passed into our range via min. This is one.
            result.set_is_min(True)
            break
        elif (looking_for == self.LOOKING_FOR_MAX) or (looking_for == self.LOOKING_FOR_BOTH):
          # check to see if it's the edge
          if (prev_minmax[1] != LogLocation.TOO_HIGH) and (result.get_rel_to_max() == LogLocation.TOO_HIGH):
            # We passed out of range. This loc is where we want to /stop/ reading. Save it!
            result.set_is_max(True)
            break
  
        # Check to see if we can short-circuit this loop due to already being too high
        if result.get_minmax() == LogLocation.OUT_OF_RANGE_HIGH:
          break
  
        prev_minmax = result.get_minmax()
        # find the next newline so we can find the next timestamp
        nl_index = chunk[chunk_loc:].find('\n')
        if nl_index == -1:
  #        DBG("can't find new line") # DEBUG
          break # Can't find a newline; we're done.
        chunk_loc += nl_index + 1 # +1 to get past newline char
      except NotTime: # not a time string found
  #      DBG("time parse error") # DEBUG
        # we're ok with occasional non-time string lines. Might start the read in the middle of a line, for example.
        # find the next newline so we can find the next timestamp
  
        # We errored, so find the next newline...
        nl_index = chunk[chunk_loc:].find('\n')
        if nl_index == -1:
  #        DBG("can't find new line") # DEBUG
          break # Can't find a newline; we're done.
        chunk_loc += nl_index + 1 # +1 to get past newline char
    
    ###
    # Edge Cases
    ###
  
    # if we read to the end of our LOOKING_FOR_MAX chunk, and don't find the in range or match -> too high edge,
    # then the_guess max IS the boundry max.
    if not result.get_is_boundry() and (looking_for == self.LOOKING_FOR_MAX) and (chunk_loc == end_loc):
      result.set_loc(guess.get_loc())
      result.set_time(guess.get_time())
      result.set_minmax(guess.get_rel_to_min(), guess.get_rel_to_max())
      result.set_is_max(True)
  
    # if we read a chunk at the end of the file, searched through that, and didn't come up with a min or max,
    # set the max to eof.
    if not result.get_is_boundry() and at_eof and \
        ((looking_for == self.LOOKING_FOR_MAX) or (looking_for == self.LOOKING_FOR_BOTH)):
      result.set_loc(seek_loc + len(chunk))
      result.set_time(time)
      result.set_minmax(logloc.time_cmp(time, times[0]), logloc.time_cmp(time, times[1]))
      result.set_is_max(True)
  
    # If we're only looking for the min, and we hit eof and didn't find it... Well, it's not there, man. Sorry.
    if not result.get_is_min() and at_eof and (looking_for == self.LOOKING_FOR_MIN):
      result.set_loc(seek_loc + len(chunk))
      result.set_time(time)
      result.set_minmax(logloc.time_cmp(time, times[0]), logloc.time_cmp(time, times[1]))
      result.set_is_min(True)
  
  #  DBG(result) # DEBUG
    return result
  
  #--------------------------------------------------------------------------------------------------------------------
  # parse_time: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
  #--------------------------------------------------------------------------------------------------------------------
  def parse_time(self, time_str):
    """Tries to parse string into a datetime object.
  
    Inputs:
      time_str - timestamp from log, formatted like: "Feb 13 18:31:36". Will ignore extra junk at end.
  
    Returns:
      datetime - datetime representation of time_str, set to the current year
  
    Raises:
      NotTime - error parsing string into datetime
    """
    # split the string on the whitespace, e.g. ["Feb", "14", "05:52:12", "web0"]
    # join the first three back together again with ' ' as the seperator
    # parse the thing!
    just_timestamp = ' '.join(time_str.split()[:config.LOG_TIMESTAMP_PARTS])
  
    # parse with the illustrious strptime
    try:
      return datetime.strptime(just_timestamp + str(datetime.now().year), "%b %d %H:%M:%S%Y")
    except ValueError:
      raise NotTime("Could not parse timestamp.", time_str)
  
  #--------------------------------------------------------------------------------------------------------------------
  # update_guess: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
  #--------------------------------------------------------------------------------------------------------------------
  def update_guess(self, guess):
    """Updates the self.boundaries list based on the guess.
  
    Inputs:
      guess           - A LogLocation that may or may not be better than the current guesses.
  
    Updates in place:
      self.boundaries - List in form [min, max] of current best guesses (outter bounds) of LogLocation entries
  
    Returns: 
      Boolean - True if self.boundaries improved, otherwise False
  
    Raises:  Nothing
    """
    improved = False
  
    if guess.get_is_min() == True: # set to min 'guess' if it's the Real Actual min boundry
      self.boundaries[0] = guess
      improved = True
  
    elif guess.get_is_max() == True: # set to max 'guess' if it's the Real Actual max boundry
      self.boundaries[1] = guess
      improved = True
  
    elif guess.get_rel_to_min() == LogLocation.TOO_LOW: # not far enough
      # Compare with min, replace if bigger
      if guess.get_loc() > self.boundaries[0].get_loc():
        self.boundaries[0] = guess
        improved = True
  
    elif guess.get_rel_to_max() == LogLocation.TOO_HIGH: # too far
      # Compare with max, replace if smaller
      if guess.get_loc() < self.boundaries[1].get_loc():
        self.boundaries[1] = guess
        improved = True
  
    return improved
  
  #--------------------------------------------------------------------------------------------------------------------
  # print_log_lines: I like comments before my functions because I'm used to C++ and not to Python!~ Herp dedurp dedee.~
  #--------------------------------------------------------------------------------------------------------------------
  def print_log_lines(self, writable=sys.stdout):
    """Prints to stdout the range of the log indicated by self.boundaries.
  
    Inputs:
      writable - writable object to print output to
  
    Returns: Nothing
  
    Raises:  Nothing
    """
    start_loc = self.boundaries[0].get_loc()
    self.log.seek(start_loc)
    stats.seeks += 1
  
    end_loc = self.boundaries[1].get_loc()
  
    # Print out the logs in question in chunks, so that we don't use too much memory.
    curr = start_loc
    while curr < end_loc:
      # only print up to the end of our range
      chunk_size = 0
      if curr + config.MAX_PRINT_CHUNK_SIZE <= end_loc:
        chunk_size = config.MAX_PRINT_CHUNK_SIZE
      else:
        chunk_size = end_loc - curr
  
      chunk = self.log.read(chunk_size)
      stats.reads += 1
      stats.print_reads += 1
      curr += chunk_size
    
      writable.write(chunk) # NOT A DEBUG STATEMENT! LEAVE ME IN!!!
      stats.print_size += chunk_size
  #    DBG((chunk_size, end_loc - start_loc)) # DEBUG
  #    DBG((start_loc, curr, end_loc)) # DEBUG
  
  #--------------------------------------------------------------------------------------------------------------------
  # input_time_parse: Parses time from command line args
  #--------------------------------------------------------------------------------------------------------------------
  def input_time_parse(self, input, first_time):
    """Parses time that  was input from command line args
  
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
      raise RegexError("Something went wrong with the regex.", config.TIME_REGEX, input)
  
    retval = []
    lacking_secs = False
    for time in times[0]:
      if time == '':
        continue # they only passed in one time, not a range
      lacking_secs = False 
      arr = time.split(':')
  
      if len(arr) == 2: # no seconds
        arr.append(0)
        lacking_secs = True
      t = first_time.replace(hour=int(arr[0]), minute=int(arr[1]), second=int(arr[2]), microsecond=0)
  
      retval.append(t)
    
    # if only one time was specified, stick a second one in to round out the [min, max] list.
    if len(retval) == 1:
      retval.append(retval[0])
  
    # if no seconds were requested, they want a range of a minute, so append one with 59 secs
    if lacking_secs:
      retval[1] = retval[1].replace(second=int(59))
  
  #  DBG(retval) # DEBUG
    return retval


#======================================================================================================================
# Functions that are Cool enough not to need a class
#======================================================================================================================
  
#----------------------------------------------------------------------------------------------------------------------
# pretty_size: I'm so pretty~ Oh so pretty~
#----------------------------------------------------------------------------------------------------------------------
def pretty_size(num):
  """Returns a string of the input bytes, prettily formatted for human reading. E.g. 2048 -> '2 KiB'"""
  for x in ['bytes','KiB','MiB','GiB','TiB', 'PiB', 'EiB', 'ZiB', 'YiB']:
    if num < 1024.0:
      return "%3.1f %s" % (num, x)
    num /= 1024.0

#----------------------------------------------------------------------------------------------------------------------
# Sometimes you just want to make the voices go away...
#----------------------------------------------------------------------------------------------------------------------
def DBG(printable):
  """No one likes bugs..."""
  if config.DEBUG:
    print printable





#----------------------------------------------------------------------------------------------------------------------
# Almost there...
#----------------------------------------------------------------------------------------------------------------------
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
#======================================================================================================================
#----------------------------------------------------------------------------------------------------------------------
#                                                    The Main Event
#----------------------------------------------------------------------------------------------------------------------
#======================================================================================================================
if __name__ == '__main__':
  # Setup arg parser
  parser = OptionParser(usage = usage)
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
  # Decide which to used...
  config_file = ''
  if isinstance(options.configfile, basestring):
    if os.path.isfile(options.configfile):
      config_file = options.configfile
    else:
      parser.error("Config file '%s' does not exist." % options.configfile)
  else:
    config_file = DEFAULT_CONFIG

  # Load the config file
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
  grepper = LogSearch(the_time, the_log)
  grepper.tgrep(options.binary_search) # grep the file

  ###
  # print statistics
  ###
  writable = sys.stdout
  if options.verbose_error or options.super_verbose_error:
    writable = sys.stderr
  if options.verbose or options.verbose_error or options.super_verbose or options.super_verbose_error:
    total_time = None
    if (stats.find_time != None) and (stats.print_time != None):
      total_time = stats.find_time + stats.print_time
    print >>writable, "\n\n -- statistics --"
    print >>writable, "seeks: %8d" % stats.seeks
    print >>writable, "reads: %8d (total)" % stats.reads
    print >>writable, "reads: %8d (just for printing)" % stats.print_reads
    print >>writable, "wide sweep loops: %4d (TAB or binary search)" % stats.wide_sweep_loops
    print >>writable, "edge sweep loops: %4d (linear search)" % stats.edge_sweep_loops
    print >>writable, "wide sweep time:  %s" % stats.wide_sweep_time
    print >>writable, "edge sweep time:  %s" % stats.edge_sweep_time
    print >>writable, "find  time:       %s" % stats.find_time
    print >>writable, "print time:       %s" % stats.print_time
    print >>writable, "total time:       %s" % total_time
    print >>writable, "amount printed:   %s" % pretty_size(stats.print_size)
    print >>writable, "log file size:    %s" % stats.file_size

  if options.super_verbose or options.super_verbose_error:
    print >>writable, "refocused wide sweep loops: %4d" % stats.refocused_wide_sweep_loops
    print >>writable, "edge sweep searched: %s" % pretty_size(stats.edge_sweep_size)
    print >>writable, "wide sweep locs: "
    print >>writable, stats.wide_sweep_end_locs
    print >>writable, "final locs: "
    print >>writable, stats.final_locs
    print >>writable, "requested times: "
    if stats.requested_times == []:
      print >>writable,  stats.requested_times      
    else:
      print >>writable, "[%s, %s]" % (str(stats.requested_times[0]), str(stats.requested_times[1]))

# Fin
