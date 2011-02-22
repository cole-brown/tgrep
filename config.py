####
###
##
# Don't delete stuff unless you want an error...
##
###
####

from extra import Configuration, Statistics

###
# Gentlemen, set your window width to 120 characters. You have been warned.
###


#----------------------------------------------------------------------------------------------------------------------
# config
#----------------------------------------------------------------------------------------------------------------------
LOG_LINE_BYTES = 500 # size of an average log line
A_GOOD_CHUNK_TO_READ = 4096 * 50 # bytes (200 KB) 
CLOSE_ENOUGH = 3000 * LOG_LINE_BYTES # bytes (within ~3000 log entries)
config = Configuration(
  # Path to log to default to if none is specified on the command line.
  DEFAULT_LOG = "/logs/haproxy.log",

  # used to calculate a second's worth of bytes
  BYTES_PER_SECOND_FUDGE_FACTOR = 1.2, 

  # Must be more than the max log line by the length of the timestamp. Used in initial binary time-adjusted search for
  # reading chunks of the file. Must be more than one line so it can find a newline and find the timestamp after it.
  MORE_THAN_ONE_LINE = LOG_LINE_BYTES * 3, # bytes
  
  # The size of the timestamp in bytes. "Feb 13 18:31:36" is 15 bytes for ASCII. Bump this up if you're modifying
  # this to work with unicode. You're allowed to go over without penalty (except file read time); don't go under.
  LOG_TIMESTAMP_SIZE = 20, # bytes
  LOG_TIMESTAMP_PARTS = 3, # "Feb", "13", "18:31:36"

  # If the time-adjusted binary search hits inside the region of desired logs, it's not much help. We need mins and
  # maxes. This is how much to move the out by (out from the focus towards lower or upper bound). Closer to 0 makes the
  # search faster & more aggressive, but too close makes wide sweep's time-adjusted binary search fail too fast and
  # leaves too much of the log for edge sweep to chug through linearly.
  REFOCUS_FACTOR = 0.15, # 15%

  # The initial binary time-adjusted search will quit once it's either this close (in bytes) or stabalized.
  WIDE_SWEEP_CLOSE_ENOUGH = CLOSE_ENOUGH, # bytes. 
  
  # Amount (in bytes) of the file that the edge-finding algorithm will read in at a time. Higher /might/ give better
  # speed but will also use more memory.
  EDGE_SWEEP_CHUNK_SIZE = A_GOOD_CHUNK_TO_READ, # bytes
  
  # Amount (in bytes) of the file that will be read and printed at a time. Higher should give better speed but
  # will use more meory.
  MAX_PRINT_CHUNK_SIZE = 3*1024*1024, # bytes 
  
  # This is the regex for the acceptable input format for times. Don't fuck it up.
  # Good:
  #   1:2:3
  #   22:33
  #   23:33:11
  #   23:33-23:33:1
  #   23:33:1-23:33
  #   23:33:1-23:33:1
  #   23:33:11-23:33:11
  #
  # Bad:
  #   23:33:-23:33
  #   23:33-23:33:
  #   23:33:-23:33:
  #   22:33:44:1
  TIME_REGEX = r'^((?:\d{1,2}:){1,2}\d{1,2})(?:-((?:\d{1,2}:){1,2}\d{1,2}))?$',
  
  # Sometimes two different sections of a log will match a supplied time range. For example, the log file goes from Feb
  # 12 06:30 to Feb 13 07:00, and the user asks for logs with timestamp 6:50. That's in both the Feb 12 and Feb 13 parts
  # of the file. How do you want these seperated when they're printed out?
  DOUBLE_MATCH_SEP = '\n\n\n', # use '' for no seperator; don't forget the \n if you want one

  # Don't turn this on. Seriously... Unless you want to debug and all the debug prints are on your branch.
  DEBUG = False,

  # May break tgrep. May make it go faster... May do nothing at all.
  EXPERIMENTAL = True # Currently switches to binary search when time search can't do any better. Sometimes helps.
)


#----------------------------------------------------------------------------------------------------------------------
# stats: This is what you get when you use -v 
#----------------------------------------------------------------------------------------------------------------------
stats = Statistics(
  # Here FYI. I guess you can change if you want to throw off your statistics...
  # Set seeks and reads to -20 and see how awesome I do!

  # regular verbosity statistics
  seeks = 0,
  reads = 0, # total
  print_reads = 0, # print-only
  wide_sweep_loops = 0, # total
  edge_sweep_loops = 0,
  wide_sweep_time  = None,
  edge_sweep_time  = None,
  find_time  = None,
  print_time = None,
  print_size = 0, # bytes
  file_size = '0 bytes',

  # extra verbosity statistics
  edge_sweep_size = 0, # bytes
  refocused_wide_sweep_loops = 0,
  binary_wide_sweep_loops = 0,
  requested_times = [],
  wide_sweep_end_locs = [],
  final_locs = []
)
