"""tgrep: grep HAproxy logs by timestamp, assuming logs are fully sorted

Usage: 
  //!

"""

requirements = """
1. It has to give the right answer, even in all the special cases. (For extra credit, list all the special cases you can think of in your README)

2. It has to be fast. During testing, keep count of how many times you call lseek() or read(), and then make those numbers smaller. (For extra credit, give us the big-O analysis of the typical case and the worst case)

3. Elegant code is better than spaghetti.

By default it uses /logs/haproxy.log as the input file, but you can specify an alternate filename by appending it to the command line. It also works if you prepend it, because who has time to remember the order of arguments for every little dumb script?
"""

__authors__ =   ['reddit@spydez.com (Cole Brown (spydez))']

# Python imports
import os

# local imports


# constants
MORE_THAN_ONE_LINE = 500 # bytes
SEEK_BYTES = 376*9000 + 50

DEFAULT_LOG = "loggen.log" # //! "/log/haproxy.log" 

def doShit():
  children = []
  
  for job in jobs:
      child = os.fork()
      if child:
          children.append(child)
      else:
          pass  # really should exec the job
  for child in children:
      os.waitpid(child, 0)

if __name__ == '__main__':
  doShit() # //! change this...

  # parse input
  # figure out which file to open
  # figure out the time range
  # don't care about arg order
