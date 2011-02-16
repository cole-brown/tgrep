from extra import Configuration, Statistics

# Don't delete stuff unless you want an error...

#----------------------------------------------------------------------------------------------------------------------
# config
#----------------------------------------------------------------------------------------------------------------------
LOG_LINE_BYTES = 377
config = Configuration(
  # Path to log to default to if none is specified on the command line.
  DEFAULT_LOG = "loggen.log", # //! "/log/haproxy.log" 

  # Used to estimate where in the log file a particular timestamp is.
  AVG_LOG_SIZE = LOG_LINE_BYTES, # bytes. That's the size of the one line I got to see in the post, anyways. 
  APPROX_MAX_LOGS_PER_SEC = 0.3, # //!1500
  APPROX_MIN_LOGS_PER_SEC = 0, # //! 500
  LOGS_PER_SEC_FUDGE_FACTOR = 1.2,
  
  # Must be more than the max log line by the length of the timestamp. Used in initial binary time-based search for
  # reading chunks of the file. Must be more than one line so it can find a newline and find the timestamp after it.
  MORE_THAN_ONE_LINE = LOG_LINE_BYTES * 3, # bytes
  
  # The size of the timestamp in bytes. "Feb 13 18:31:36" is 15 bytes for ASCII. Bump this up if you're modifying
  # this to work with unicode. You're allowed to go over without penalty (except file read time); don't go under.
  LOG_TIMESTAMP_SIZE = 20, # bytes
  LOG_TIMESTAMP_PARTS = 3, # "Feb", "13", "18:31:36"
  
  # The initial binary time-based search will quit once it's either this close (in bytes) or stabalized.
  WIDE_SWEEP_CLOSE_ENOUGH = 2048, # bytes. //! bump this up 2k is small.
  
  # Amount (in bytes) of the file that the edge-finding algorithm will read in at a time. Higher /might/ give better
  # speed but will also use more memory.
  EDGE_SWEEP_CHUNK_SIZE = 2048, # bytes //! bump this up! 2k is small...
  EDGE_SWEEP_PESSIMISM_FACTOR = 3, # curr * this > expected? Then we act all sad.
  
  # Amount (in bytes) of the file that will be read and printed at a time. Higher should give better speed but
  # will use more meory.
  MAX_PRINT_CHUNK_SIZE = 2048, # bytes //! bump this up 2k is small...
  
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
  
  # Maximum size in bytes of mmap-able region.
  MAX_MMAP_SIZE = 1 * 1024 * 1024, # 1 MB //! get page size in here  
)


#----------------------------------------------------------------------------------------------------------------------
# stats: This is what you get when you use -v 
#----------------------------------------------------------------------------------------------------------------------
stats = Statistics(
  # Here FYI. I guess you can change if you want to throw off your statistics...
  # Set seeks and reads to -20 and see how awesome I do!
  seeks = 0,
  reads = 0, # total
  print_reads = 0, # print-only
  wide_sweep_loops = 0,
  edge_sweep_loops = 0,
  wide_sweep_time  = None,
  edge_sweep_time  = None,
  find_time  = None,
  print_time = None
)




