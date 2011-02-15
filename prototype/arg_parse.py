#!/usr/bin/env python2.6
#

from optparse import OptionParser
import re
from datetime import datetime

# The only required arg is time
REQUIRED_NUM_ARGS = 1

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
TIME_REGEX = r'^((?:\d{1,2}:){1,2}\d{1,2})-?((?:\d{1,2}:){1,2}\d{1,2})?$'


def t_r(input):
  time_regex = re.compile(TIME_REGEX, re.IGNORECASE) 
  times = time_regex.findall(input) # returns [(group1, group2)] for my regex
  if times == []:
    # Raise the alarm! No regex match!
    print "NO MATCH!" # DEBUG
    return #//! raise something?
  elif 0 < times[0] < 3:
    # Something's wrong with the regex. Only supposed to get 1 or 2 matches.
    print "REGEX BUG!" # DEBUG
    return #//! raise something?
  retval = []
  lacking_secs = False
  for time in times[0]:
    if time == '':
      continue # they only passed in one time, not a range
    lacking_secs = False # when have 2 times, don't care if first lacks seconds
    arr  = time.split(':')
    date = datetime.now()
    #//! We'll have to roll back the day to whatever the log starts with, + 1 if it's "before" the log starts
    # (and thus actually the next day). Use timedelta to get around new year's and such.
    # No, wait. Use first_time. Then replace h:m:s, then roll back if needed.
    if len(arr) == 2: # no seconds
      arr.append(0)
      lacking_secs = True
    retval.append(date.replace(hour=int(arr[0]), minute=int(arr[1]), second=int(arr[2]), microsecond=0))
  
  # if only one date was specified, stick a second one in to round out the [min, max] list.
  if len(retval) == 1:
    retval.append(retval[0])

  # if no seconds were requested, they want a range of a minute, so append one with 59 secs
  if lacking_secs:
    retval[1] = retval[1].replace(second=int(59))

  print retval # DEBUG
  return retval
  


#----------------------------------------------------------------------------------------------------------------------
#                                                    The Main Event
#----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  usage = """Usage: times
   Or: times [file]\n   Or: times [options] [file]\n   Or: [options] times [file]
   Or: [options] [file] times\n...I don't really care; do whatever you want. Just gimme my times."""
  parser = OptionParser(usage = usage)
  parser.add_option("-v", "--verbose",
                    action="store_true", dest="verbose", default=False,
                    help="print out statistics at end of run")
  
  (options, args) = parser.parse_args()

  if len(args) < REQUIRED_NUM_ARGS:
    parser.error("Missing the required 'times' argument.")
    # exit stage right w/ help message and that string
  
  print "blah blah blah"

  if options.verbose:
    print "statistics blah blah blah"

  print '23:33:1'
  t_r('23:33:1')
  print '23:33:11'
  t_r('23:33:11')
  print '23:33'
  t_r('23:33')
  print '1:2:3-4:5:6'
  t_r('1:2:3-4:5:6')
  print '23:33:11-23:33:30'
  t_r('23:33:11-23:33:30')
  print '23:33-23:33'
  t_r('23:33-23:33')
  print '23:33:1-23:33:1'
  t_r('23:33:1-23:33:1')
  print '23:33:-23:33'
  t_r('23:33:-23:33')
  print '23:33:-23:33:'
  t_r('23:33:-23:33:')
  print '23:33:1:1-23:33:1'
  t_r('23:33:1:1-23:33:1')
