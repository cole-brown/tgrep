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


# Python imports
import os
from datetime import datetime
import unittest

# local imports
import tgrep




#----------------------------------------------------------------------------------------------------------------------
#                                                    TgrepTestCase
#----------------------------------------------------------------------------------------------------------------------
class TgrepTestCase(unittest.TestCase):
  def setUp(self):
    self.log_file = open("tests/data/loggen.log", 'rb')

  def tearDown(self):
    self.log_file.close()

  def test_bsg(self):
    self.assertEquals(  5, tgrep.binary_search_guess(0,   10))
    self.assertEquals( 50, tgrep.binary_search_guess(0,  100))
    self.assertEquals(500, tgrep.binary_search_guess(0, 1000))
    self.assertEquals(279, tgrep.binary_search_guess(337, 222)) # actually is 279.5, testing round
    self.assertEquals(496918739, tgrep.binary_search_guess(0, 993837478))

  def test_tsg(self):
    #//! impl
    self.assertEquals(1,1)

  def test_fts(self):
    # Feb 13 18:31:30
    fts = datetime(datetime.now().year, 2, 13, 18, 31, 30)
    self.assertEquals(fts, tgrep.first_timestamp(self.log_file))

  def test_ps(self):
    self.assertRaises(ValueError, tgrep.parse_time, time_str="this is an invalid date")
    self.assertRaises(ValueError, tgrep.parse_time, time_str="Feb 13 18:31:300") # 300 sec
    self.assertRaises(ValueError, tgrep.parse_time, time_str="March 13 18:31:30") # Full month
    self.assertRaises(ValueError, tgrep.parse_time, time_str="Feb 13 18:31") # no secs
    self.assertRaises(ValueError, tgrep.parse_time, time_str="Feb 13 18:31:ab")
    self.assertRaises(ValueError, tgrep.parse_time, time_str="Feb 13 , 18:31:30")
    self.assertRaises(ValueError, tgrep.parse_time, time_str="Feb 13, 18:31:30")
    self.assertRaises(ValueError, tgrep.parse_time, time_str="Feb 29 18:31:30") # day
    self.assertEquals(tgrep.parse_time("Feb 13 18:31:30"), datetime(datetime.now().year,  2, 13, 18, 31, 30))
    self.assertEquals(tgrep.parse_time("Jan 29 00:31:30"), datetime(datetime.now().year,  1, 29,  0, 31, 30))
    self.assertEquals(tgrep.parse_time("Oct 31  1:00:00"), datetime(datetime.now().year, 10, 31,  1,  0,  0))
    self.assertEquals(tgrep.parse_time("Apr 26 19:08:04"), datetime(datetime.now().year,  4, 26, 19,  8,  4))

  def test_es(self):
    # Really... it's a simple calculation. Based on config params. Can't test it without reimplemnting it.
    pass





#----------------------------------------------------------------------------------------------------------------------
#                                                    The Main Event
#----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  print "foo"
#  suite = unittest.TestLoader().loadTestsFromTestCase(TestSequenceFunctions)
#  unittest.TextTestRunner(verbosity=2).run(suite)
