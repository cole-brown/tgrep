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

Make sure it works on >4 GB files. Mostly the seek func. Python natively supports big ints.

README.
  O(log2). Other analysis. Number of children. Speed.
  http://backyardbamboo.blogspot.com/2009/02/python-multiprocessing-vs-threading.html
  Tested on OS X 10.6.y in Python 2.6.z
  Tested on raldi's generated log, my generated log, and a >4 GB file

Notes:
  http://docs.python.org/library/multiprocessing.html
  http://docs.python.org/library/queue.html#Queue.Queue
  http://docs.python.org/library/os.html
  http://docs.python.org/release/2.4.4/lib/bltin-file-objects.html
"""

# Python imports
import os
from multiprocessing import Process, Queue
from datetime import datetime

# local imports


# constants
MORE_THAN_ONE_LINE = 500 # bytes
SEEK_BYTES = 376*9000 + 50

DEFAULT_LOG = "h.txt"#"loggen.log" # //! "/log/haproxy.log" 

def doShit2(path_to_log):
  # whine if log file doesn't exists
  if not os.path.isfile(path_to_log):
    print "file '%s' does not exist" % path_to_log

  # for single vs multi, just bump guesses down to 1.
  seek_guesses = [2,4]
  guess_times  = Queue()
  children = []
  with open(path_to_log, 'r') as log:
    for seek_loc in seek_guesses:
      p = Process(target=workerBee, args=(log,seek_loc,guess_times))
      p.start()
      children.append(p)
    for child in children:
      child.join()
      print guess_times.get()
    
def workerBee(file, seek_loc, guess_times):
  file.seek(seek_loc)
  guess_times.put([seek_loc, file.read(2)]) # read more

def time_cmp(time_str, desired):
  log_time = datetime.strptime(time_str + str(datetime.now().year), "%b %d %H:%M:%S%Y")
  print "log: ", 
  print log_time
  print "desired: ",
  print desired
  if log_time > desired:
    return 1 # 1 means "KEEP GOING DUDE!"
  elif log_time == desired:
    return 0 # Aw, yeah. We're awesome.
  else:
    return -1 # Too far! Pull back!

def doShit(path_to_log):
  children = []

  # whine if log file doesn't exists
  if not os.path.isfile(path_to_log):
    print "file '%s' does not exist" % path_to_log

  # //! state assumptions
  seek_guesses = [0,0,0]
  seek_g2 = []

  with open(path_to_log, 'r') as log: 
#    log.seek(SEEK_BYTES)
    for seek_loc in seek_guesses:
      pid = os.fork()
      if pid is not 0: # this is the parent 
        children.append(pid)
      else: # these are the children
        log.seek(0)
        chunk = log.read(2)
#       chunk = log.read(MORE_THAN_ONE_LINE)
        print chunk
        chunk = log.read(2)
        print chunk
        # find next date, compare
        seek_g2.append(42)
        os._exit(0)
  
    for child in children:
      os.waitpid(child, 0)



if __name__ == '__main__':
  now = datetime.today() # today() instead of now() to lose TZ info
  now.replace(microsecond=0)
  # get min and max via min=now and replace()
  min = datetime(2011, 2, 1, 13, 34, 43)
  print time_cmp("Feb  9 14:34:43", min)
  min = datetime(2011, 2, 9, 14, 34, 43)
  print time_cmp("Feb  9 14:34:43", min)
  min = datetime(2011, 2, 9, 15, 34, 43)
  print time_cmp("Feb  9 14:34:43", min)

#  doShit2(DEFAULT_LOG) # //! change this...

  # parse input
  # figure out which file to open
  # figure out the time range
  # don't care about arg order