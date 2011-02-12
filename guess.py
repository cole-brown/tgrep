#!/usr/bin/env python2.6
#

class Guess:
  """//! class description!"""
  # //! vars? min/max, that sort of thing?

  # for _relation_to_desired_min/max
  TOO_LOW  = -1
  TOO_HIGH =  1
  MATCH    =  0

  # for get_minmax compare
  OUT_OF_RANGE_HIGH = [TOO_HIGH, TOO_HIGH] 
  OUT_OF_RANGE_LOW  = [TOO_LOW,  TOO_LOW]
  IN_RANGE          = [TOO_HIGH, TOO_LOW] # above the min, but below the max
  MATCHES_MIN       = [MATCH,    TOO_LOW]
  MATCHES_MAX       = [TOO_HIGH, MATCH]
  EXACT_MATCH       = [MATCH,    MATCH]

  def __init__(self, seek_loc, datetime, min, max):
    """bah blah"""
    self._seek_loc  = seek_loc
    self._timestamp = datetime
    self._relation_to_desired_min = min
    self._relation_to_desired_max = max

  def __repr__(self):
    """print to repl"""
    return "[%d, %s, %d, %d]" % (self._seek_loc, str(self._timestamp), \
                                 self._relation_to_desired_min, self._relation_to_desired_min)

  def __str__(self):
    """stringify"""
    return "[%d, %s, %d, %d]" % (self._seek_loc, str(self._timestamp), \
                                 self._relation_to_desired_min, self._relation_to_desired_min)

  def get_minmax(self):
    """tuple of min/max"""
    return self._relation_to_desired_min, self._relation_to_desired_max

  def set_minmax(self, min, max):
    self._relation_to_desired_min = min
    self._relation_to_desired_max = max

  def time_cmp(cls, log_time, desired):
    if log_time > desired:
      return Guess.TOO_HIGH # Too far into the log! Pull back!
    elif log_time == desired:
      return Guess.MATCH # Aw, yeah. We're awesome.
    else:
      return Guess.TOO_LOW # KEEP GOING DUDE!
  time_cmp = classmethod(time_cmp)




if __name__ == '__main__':
  #now = datetime.today() # today() instead of now() to lose TZ info
  print "boo"
