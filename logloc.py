#!/usr/bin/env python2.6
#

"""logloc: LogLocation class stores data related to locations/times in a log."""

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

#----------------------------------------------------------------------------------------------------------------------
#                                                     LogLocation
#----------------------------------------------------------------------------------------------------------------------
class LogLocation:
  """//! class description!"""

  # for _relation_to_desired_min/max
  TOO_LOW  = -1
  TOO_HIGH =  1
  MATCH    =  0

  # for get_minmax compare
  OUT_OF_RANGE_HIGH = (TOO_HIGH, TOO_HIGH) 
  OUT_OF_RANGE_LOW  = (TOO_LOW,  TOO_LOW)
  IN_RANGE          = (TOO_HIGH, TOO_LOW) # above the min, but below the max
  MATCHES_MIN       = (MATCH,    TOO_LOW)
  MATCHES_MAX       = (TOO_HIGH, MATCH)
  EXACT_MATCH       = (MATCH,    MATCH)
  INVALID           = (TOO_LOW, TOO_HIGH)

  def __init__(self, file_loc, datetime, min, max):
    """bah blah"""
    self._file_loc  = file_loc
    self._timestamp = datetime
    self._relation_to_desired_min = min
    self._relation_to_desired_max = max
    self._is_min_boundry = False
    self._is_max_boundry = False

  def __repr__(self):
    """print to repl"""
    return "[%d, %s, %d, %d, %s, %s]" % (self._file_loc, str(self._timestamp), \
                                         self._relation_to_desired_min, self._relation_to_desired_max, \
                                         self._is_min_boundry, self._is_max_boundry)

  def __str__(self):
    """stringify"""
    return "[%d, %s, %d, %d, %s, %s]" % (self._file_loc, str(self._timestamp), \
                                         self._relation_to_desired_min, self._relation_to_desired_max, \
                                         self._is_min_boundry, self._is_max_boundry)

  def get_minmax(self):
    """tuple of min/max"""
    return self._relation_to_desired_min, self._relation_to_desired_max

  def set_minmax(self, min, max):
    self._relation_to_desired_min = min
    self._relation_to_desired_max = max

  def get_rel_to_min(self):
    """relation to min"""
    return self._relation_to_desired_min

  def set_rel_to_min(self, rel):
    self._relation_to_desired_min = rel

  def get_rel_to_max(self):
    """relation to max"""
    return self._relation_to_desired_max

  def set_rel_to_max(self, rel):
    self._relation_to_desired_max = rel

  def set_is_min(self, b):
    self._is_min_boundry = b

  def set_is_max(self, b):
    self._is_max_boundry = b

  def get_is_min(self):
    return self._is_min_boundry

  def get_is_max(self):
    return self._is_max_boundry

  def get_is_boundry(self):
    return self._is_min_boundry or self._is_max_boundry

  def get_loc(self):
    return self._file_loc

  def set_loc(self, file_loc):
    self._file_loc = file_loc

  def get_time(self):
    return self._timestamp

  def set_time(self, timestamp):
    self._timestamp = timestamp



#----------------------------------------------------------------------------------------------------------------------
#                                                         >.>
#----------------------------------------------------------------------------------------------------------------------
def time_cmp(log_time, desired):
  if log_time > desired:
    return LogLocation.TOO_HIGH # Too far into the log! Pull back!
  elif log_time == desired:
    return LogLocation.MATCH # Aw, yeah. We're awesome.
  else:
    return LogLocation.TOO_LOW # KEEP GOING DUDE!





#----------------------------------------------------------------------------------------------------------------------
#                                                    The Main Event
#----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  # do nothing
  pass
