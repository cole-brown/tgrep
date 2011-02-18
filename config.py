

# Don't delete stuff unless you want an error...


from extra import Configuration, Statistics

###
# Gentlemen, set your window width to 120 characters. You have been warned.
###


#----------------------------------------------------------------------------------------------------------------------
# config
#----------------------------------------------------------------------------------------------------------------------
LOG_LINE_BYTES = 377
A_GOOD_CHUNK_TO_READ = 4096 * 10 # bytes //! bump this up?
config = Configuration(
  # Path to log to default to if none is specified on the command line.
  DEFAULT_LOG = "loggen.log", # //! "/log/haproxy.log" 

  # Used to estimate where in the log file a particular timestamp is.
  AVG_LOG_SIZE = LOG_LINE_BYTES, # bytes. That's the size of the one line I got to see in the post, anyways. 
  APPROX_MAX_LOGS_PER_SEC = 0.3, # //!1500
  APPROX_MIN_LOGS_PER_SEC = 0, # //! 500
  LOGS_PER_SEC_FUDGE_FACTOR = 1.2, # //! am I using any of these?

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
  # maxes. This is how much to move the out by (out from the focus towards lower or upper bound).  seek loc to reel back
  # the search.
  REFOCUS_FACTOR = 0.75,

  # Maximum number of times to hit inside the range once time-adjusted binary search has gone into slower mode.
  # This will be applied independently to the upper and lower bounds of the search.
  WIDE_SWEEP_MAX_RANGE_HITS = 1,

  # The initial binary time-adjusted search will quit once it's either this close (in bytes) or stabalized.
  WIDE_SWEEP_CLOSE_ENOUGH = 8128, # bytes. //! adjust to ~(1500-500)/2*log_size
  
  # Amount (in bytes) of the file that the edge-finding algorithm will read in at a time. Higher /might/ give better
  # speed but will also use more memory.
  EDGE_SWEEP_CHUNK_SIZE = A_GOOD_CHUNK_TO_READ, # bytes
  EDGE_SWEEP_PESSIMISM_FACTOR = 3, # curr * this > expected? Then we act all sad. //! used?
  
  # Amount (in bytes) of the file that will be read and printed at a time. Higher should give better speed but
  # will use more meory.
  MAX_PRINT_CHUNK_SIZE = A_GOOD_CHUNK_TO_READ, # bytes 
  
  # This is the regex for the acceptable input format for times. Don't fuck it up.
  # Good:
  #   1:2:3
  #   22:33
  #   23:33:11
  #   23:33-23:33
  #   23:33:1-23:33:1
  #   23:33:11-23:33:11
  #
  # Bad:
  #   23:33:-23:33
  #   23:33-23:33:
  #   23:33:-23:33:
  #   22:33:44:1
  # TIME_REGEX = r'^((?:\d{1,2}:){1,2}\d{1,2})-?((?:\d{1,2}:){1,2}\d{1,2})?$', # old and busted
  TIME_REGEX = r'^((?:\d{1,2}:){1,2}\d{1,2})(?:-((?:\d{1,2}:){1,2}\d{1,2}))?$', # new hotness
  
  # Sometimes two different sections of a log will match a supplied time range. For example, the log file goes from Feb
  # 12 06:30 to Feb 13 07:00, and the user asks for logs with timestamp 6:50. That's in both the Feb 12 and Feb 13 parts
  # of the file. How do you want these seperated when they're printed out?
  DOUBLE_MATCH_SEP = '\n\n\n',

  # Don't turn this on. Seriously... Unless you want to debug.
  DEBUG = True,

  # Maximum size in bytes of mmap-able region.
  MAX_MMAP_SIZE = 1 * 1024 * 1024 # 1 MB //! get page size in here  //! Ain't usin' this...
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
  refocused_wide_sweep_loops = 0,
  edge_sweep_loops = 0,
  wide_sweep_time  = None,
  edge_sweep_time  = None,
  find_time  = None,
  print_time = None,
  file_size = '0 bytes',

  # extra verbosity statistics
  requested_times = [],
  wide_sweep_end_locs = [],
  final_locs = []
)
