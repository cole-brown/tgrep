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
import StringIO

# local imports
import tgrep
import anomaly
from logloc import LogLocation




#----------------------------------------------------------------------------------------------------------------------
#                                                    TgrepTestCase
#----------------------------------------------------------------------------------------------------------------------
class TgrepTestCase(unittest.TestCase):
  def setUp(self):
    self.mlog_file = open("tests/data/my.log",   'rb')
    self.rlog_file = open("tests/data/raldi.log",'rb')
    self.log_entries = StringIO.StringIO()

  def tearDown(self):
    self.mlog_file.close()
    self.rlog_file.close()
    self.log_entries.close()

  def test_bsg(self):
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 23, 33, 11),
                      LogLocation.MATCH,
                      LogLocation.MATCH)
    max = LogLocation(10, datetime(datetime.now().year,  2, 13, 23, 33, 15),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    bounds = [min, max]
    foo = None # ignored anyways
    self.assertEquals(  5, tgrep.binary_search_guess(bounds, foo))
    bounds[1].set_loc(100)
    self.assertEquals( 50, tgrep.binary_search_guess(bounds, foo))
    bounds[1].set_loc(1000)
    self.assertEquals(500, tgrep.binary_search_guess(bounds, foo))
    bounds[0].set_loc(337)
    bounds[1].set_loc(222)
    self.assertEquals(279, tgrep.binary_search_guess(bounds, foo)) # actually is 279.5, testing round
    bounds[0].set_loc(0)
    bounds[1].set_loc(993837478)
    self.assertEquals(496918739, tgrep.binary_search_guess(bounds, foo))

  def test_tsg(self):
    #//! impl
    self.assertEquals(1,1)

  def test_fts(self):
    # Feb 13 18:31:30
    fts = datetime(datetime.now().year, 2, 13, 18, 31, 30)
    self.assertEquals(fts, tgrep.first_timestamp(self.mlog_file))

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

  def test_prn_m_0(self):
    global expected_log0

    # Feb 13 23:33:11 (one log line)
    # [[1508000, 2011-02-13 23:33:11, 0, 0, True, False], [1508377, 2011-02-13 23:33:15, 1, 1, False, True]]
    min = LogLocation(1508000, datetime(datetime.now().year,  2, 13, 23, 33, 11),
                      LogLocation.MATCH,
                      LogLocation.MATCH)
    min.set_is_min(True)
    max = LogLocation(1508377, datetime(datetime.now().year,  2, 13, 23, 33, 15),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    max.set_is_min(True)
    bounds = [min, max]
    tgrep.print_log_lines(self.mlog_file, bounds, self.log_entries)
    self.assertEquals(expected_log0, self.log_entries.getvalue())

  def test_prn_m_1(self):
    global expected_log1

    # Feb 13 23:33 (whole minute)
    # [[1507623, 2011-02-13 23:33:03, 1, -1, True, False], [1512524, 2011-02-13 23:34:03, 1, 1, False, True]]
    min = LogLocation(1507623, datetime(datetime.now().year,  2, 13, 23, 33, 3),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_LOW)
    min.set_is_min(True)
    max = LogLocation(1512524, datetime(datetime.now().year,  2, 13, 23, 34, 3),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    max.set_is_min(True)
    bounds = [min, max]
    tgrep.print_log_lines(self.mlog_file, bounds, self.log_entries)
    self.assertEquals(expected_log1, self.log_entries.getvalue())

  def test_prn_m_2(self):
    global expected_log2

    # zero bytes
    min = LogLocation(1507623, datetime(datetime.now().year,  2, 13, 23, 33, 3),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_LOW)
    min.set_is_min(True)
    max = LogLocation(1507623, datetime(datetime.now().year,  2, 13, 23, 33, 3),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH) # same log, basically
    max.set_is_min(True)
    bounds = [min, max]
    tgrep.print_log_lines(self.mlog_file, bounds, self.log_entries)
    self.assertEquals(expected_log2, self.log_entries.getvalue())

  def test_prn_m_3(self):
    global expected_log3

    # Feb 14 07:07:39 (End of File, exactly one line)
    # [[3769623, 2011-02-14 07:07:39, 0, 0, True, False], [3770000, 2011-02-14 07:07:39, 1, 1, False, True]]
    min = LogLocation(3769623, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    min.set_is_min(True)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    max.set_is_min(True)
    bounds = [min, max]
    tgrep.print_log_lines(self.mlog_file, bounds, self.log_entries)
    self.assertEquals(expected_log3, self.log_entries.getvalue())

  def test_prn_m_4(self):
    global expected_log4

    # Feb 14 07:07:39 (End of File, chunk)
    # [[3765853, 2011-02-14 07:07:01, 1, -1, True, False], [3770000, 2011-02-14 07:07:39, 1, 1, False, True]]
    min = LogLocation(3765853, datetime(datetime.now().year,  2, 14, 7, 7, 1),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_LOW)
    min.set_is_min(True)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    max.set_is_min(True)
    bounds = [min, max]
    tgrep.print_log_lines(self.mlog_file, bounds, self.log_entries)
    self.assertEquals(expected_log4, self.log_entries.getvalue())

  def test_prn_m_5(self):
    global expected_log5

    # Feb 13 18:31:30 (Start of File, exactly one line)
    # [[0, 2011-02-13 18:31:30, 0, 0, True, False], [377, 2011-02-13 18:31:36, 1, 1, False, True]]
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    min.set_is_min(True)
    max = LogLocation(377, datetime(datetime.now().year,  2, 13, 18, 31, 36),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    max.set_is_min(True)
    bounds = [min, max]
    tgrep.print_log_lines(self.mlog_file, bounds, self.log_entries)
    self.assertEquals(expected_log5, self.log_entries.getvalue())

  def test_prn_m_6(self):
    global expected_log6

    # Feb 13 18:30:30 (Start of File, chunk, no exact matches)
    # [[0, 2011-02-13 18:31:30, 1, -1, True, False], [2639, 2011-02-13 18:32:08, 1, 1, False, True]]
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_LOW)
    min.set_is_min(True)
    max = LogLocation(2639, datetime(datetime.now().year,  2, 13, 18, 32, 8),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    max.set_is_min(True)
    bounds = [min, max]
    tgrep.print_log_lines(self.mlog_file, bounds, self.log_entries)
    self.assertEquals(expected_log6, self.log_entries.getvalue())

  def test_ug_0(self):
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    guesses = [min, max]
    new = LogLocation(-10, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    answer = [min, max]
    # no update, low loc for min
    tgrep.update_guess(new, guesses)
    self.assertEquals(answer, guesses)

  def test_ug_1(self):
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    guesses = [min, max]
    new = LogLocation(1000, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    answer = [new, max]
    # update low
    tgrep.update_guess(new, guesses)
    self.assertEquals(answer, guesses)

  def test_ug_2(self):
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    guesses = [min, max]
    new = LogLocation(2220000, datetime(datetime.now().year,  2, 14, 6, 6, 6),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    answer = [min, new]
    # update high
    tgrep.update_guess(new, guesses)
    self.assertEquals(answer, guesses)

  def test_ug_3(self):
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    guesses = [min, max]
    new = LogLocation(3779999999, datetime(datetime.now().year,  2, 16, 22, 26, 26),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    answer = [min, max]
    # no update, too high
    tgrep.update_guess(new, guesses)
    self.assertEquals(answer, guesses)

  def test_ug_4(self):
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    guesses = [min, max]
    new = LogLocation(12345, datetime(datetime.now().year,  2, 13, 19, 0, 0),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_LOW)
    answer = [min, max]
    # no update, in range
    tgrep.update_guess(new, guesses)
    self.assertEquals(answer, guesses)

  def test_ug_5(self):
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    guesses = [min, max]
    new = LogLocation(1234, datetime(datetime.now().year,  2, 13, 19, 0, 0),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_LOW)
    new.set_is_min(True)
    answer = [new, max]
    # update, is_min
    tgrep.update_guess(new, guesses)
    self.assertEquals(answer, guesses)

  def test_ug_6(self):
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    guesses = [min, max]
    new = LogLocation(1234, datetime(datetime.now().year,  2, 13, 19, 0, 0),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    new.set_is_max(True)
    answer = [min, new]
    # update, is_max
    tgrep.update_guess(new, guesses)
    self.assertEquals(answer, guesses)

  def test_ug_7(self):
    #//! impl in update_guess
    return
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_LOW)
    min.set_is_min(True)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    guesses = [min, max]
    new = LogLocation(1234, datetime(datetime.now().year,  2, 13, 19, 0, 0),
                      LogLocation.TOO_LOW,
                      LogLocation.TOO_LOW)
    answer = [min, max]
    # ignore, is_min already set for min
    tgrep.update_guess(new, guesses)
    self.assertEquals(answer, guesses)

  def test_ug_8(self):
    #//! impl in update_guess
    return
    min = LogLocation(0, datetime(datetime.now().year,  2, 13, 18, 31, 30),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_LOW)
    max = LogLocation(3770000, datetime(datetime.now().year,  2, 14, 7, 7, 39),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    max.set_is_max(True)
    guesses = [min, max]
    new = LogLocation(1234, datetime(datetime.now().year,  2, 13, 19, 0, 0),
                      LogLocation.TOO_HIGH,
                      LogLocation.TOO_HIGH)
    answer = [min, max]
    # ignore, is_max already set for max
    tgrep.update_guess(new, guesses)
    self.assertEquals(answer, guesses)

  def test_pfs_0(self):
    # Feb 13 23:33 (whole minute)
    # [[1507623, 2011-02-13 23:33:03, 1, -1, True, False], [1512524, 2011-02-13 23:34:03, 1, 1, False, True]]
    a = datetime(datetime.now().year,  2, 13, 23, 33, 3)
    b = datetime(datetime.now().year,  2, 13, 23, 34, 3)
    times = [a, b]
    loc = 1507620
    answer = LogLocation(1507623, datetime(datetime.now().year,  2, 13, 23, 33, 3),
                         LogLocation.MATCH,
                         LogLocation.TOO_LOW)
    result = tgrep.pessismistic_forward_search(self.mlog_file, loc, times)
    self.assertEquals(answer, result)

  def test_pfs_1(self):
    # Feb 13 23:33 (whole minute)
    # [[1507623, 2011-02-13 23:33:03, 1, -1, True, False], [1512524, 2011-02-13 23:34:03, 1, 1, False, True]]
    a = datetime(datetime.now().year,  2, 13, 23, 33, 3)
    b = datetime(datetime.now().year,  2, 13, 23, 34, 3)
    times = [a, b]
    loc = 1512500
    answer = LogLocation(1512524, datetime(datetime.now().year,  2, 13, 23, 34, 3),
                         LogLocation.TOO_HIGH,
                         LogLocation.MATCH)
    result = tgrep.pessismistic_forward_search(self.mlog_file, loc, times)
    self.assertEquals(answer, result)

  def test_pfs_2(self):
    # Feb 13 23:33:03 (one log line)
    a = datetime(datetime.now().year,  2, 13, 23, 33, 3)
    b = datetime(datetime.now().year,  2, 13, 23, 33, 3)
    times = [a, b]
    loc = 1507620
    answer = LogLocation(1507623, datetime(datetime.now().year,  2, 13, 23, 33, 3),
                         LogLocation.MATCH,
                         LogLocation.MATCH)
    result = tgrep.pessismistic_forward_search(self.mlog_file, loc, times)
    self.assertEquals(answer, result)

  def test_pfs_3(self):
    # Feb 13 23:33 (whole minute)
    # [[1507623, 2011-02-13 23:33:03, 1, -1, True, False], [1512524, 2011-02-13 23:34:03, 1, 1, False, True]]
    a = datetime(datetime.now().year,  2, 13, 23, 33, 3)
    b = datetime(datetime.now().year,  2, 13, 23, 34, 3)
    times = [a, b]
    loc = 1509000
    answer = LogLocation(1509131, datetime(datetime.now().year,  2, 13, 23, 33, 22),
                         LogLocation.TOO_HIGH,
                         LogLocation.TOO_LOW)
    result = tgrep.pessismistic_forward_search(self.mlog_file, loc, times)
    self.assertEquals(answer, result)

  def test_pfs_4(self):
    # Feb 13 23:33 (whole minute)
    # [[1507623, 2011-02-13 23:33:03, 1, -1, True, False], [1512524, 2011-02-13 23:34:03, 1, 1, False, True]]
    a = datetime(datetime.now().year,  2, 13, 23, 33, 3)
    b = datetime(datetime.now().year,  2, 13, 23, 34, 3)
    times = [a, b]
    loc = 0
    answer = LogLocation(377, datetime(datetime.now().year,  2, 13, 18, 31, 36),
                         LogLocation.TOO_LOW,
                         LogLocation.TOO_LOW)
    result = tgrep.pessismistic_forward_search(self.mlog_file, loc, times)
    self.assertEquals(answer, result)

  def test_pfs_5(self):
    # Feb 13 23:33 (whole minute)
    # [[1507623, 2011-02-13 23:33:03, 1, -1, True, False], [1512524, 2011-02-13 23:34:03, 1, 1, False, True]]
    a = datetime(datetime.now().year,  2, 13, 23, 33, 3)
    b = datetime(datetime.now().year,  2, 13, 23, 34, 3)
    times = [a, b]
    loc = 3333333
    answer = LogLocation(3333434, datetime(datetime.now().year,  2, 14, 5, 40, 40),
                         LogLocation.TOO_HIGH,
                         LogLocation.TOO_HIGH)
    result = tgrep.pessismistic_forward_search(self.mlog_file, loc, times)
    self.assertEquals(answer, result)

  def test_atp(self):
    fts = datetime(datetime.now().year, 2, 13, 18, 31, 30)

    # Good
    answer = [datetime(datetime.now().year,  2, 14, 1, 2, 3),
              datetime(datetime.now().year,  2, 14, 1, 2, 3)]
    result = tgrep.arg_time_parse("1:2:3", fts)
    self.assertEquals(answer, result)

    answer = [datetime(datetime.now().year,  2, 13, 22, 33,  0),
              datetime(datetime.now().year,  2, 13, 22, 33, 59)]
    result = tgrep.arg_time_parse("22:33", fts)
    self.assertEquals(answer, result)

    answer = [datetime(datetime.now().year,  2, 13, 22, 33, 11),
              datetime(datetime.now().year,  2, 13, 22, 33, 11)]
    result = tgrep.arg_time_parse("22:33:11", fts)
    self.assertEquals(answer, result)

    answer = [datetime(datetime.now().year,  2, 13, 22, 33,  0),
              datetime(datetime.now().year,  2, 13, 22, 33, 59)]
    result = tgrep.arg_time_parse("22:33-22:33", fts)
    self.assertEquals(answer, result)

    answer = [datetime(datetime.now().year,  2, 13, 22,  3, 1),
              datetime(datetime.now().year,  2, 13, 22, 33, 1)]
    result = tgrep.arg_time_parse("22:3:1-22:33:1", fts)
    self.assertEquals(answer, result)

    answer = [datetime(datetime.now().year,  2, 13, 22,  3, 11),
              datetime(datetime.now().year,  2, 13, 22, 33, 11)]
    result = tgrep.arg_time_parse("22:3:11-22:33:11", fts)
    self.assertEquals(answer, result)
    
    # Bad
    self.assertRaises(anomaly.NotTime, tgrep.arg_time_parse, input="23:33:-23:33", first_time=fts)
    self.assertRaises(anomaly.NotTime, tgrep.arg_time_parse, input="23:33-23:33:", first_time=fts)
    self.assertRaises(anomaly.NotTime, tgrep.arg_time_parse, input="23:33:-23:33:", first_time=fts)
    self.assertRaises(anomaly.NotTime, tgrep.arg_time_parse, input="22:33:44:1", first_time=fts)
    self.assertRaises(anomaly.NotTime, tgrep.arg_time_parse, input="22:33:44:1-22:33", first_time=fts)
    self.assertRaises(anomaly.NotTime, tgrep.arg_time_parse, input="22:33:44-22:33:44:1", first_time=fts)
    self.assertRaises(anomaly.NotTime, tgrep.arg_time_parse, input="22", first_time=fts)
    self.assertRaises(anomaly.NotTime, tgrep.arg_time_parse, input="This test is getting out of hand.", first_time=fts)






expected_log0="""Feb 13 23:33:11 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
"""
expected_log1="""Feb 13 23:33:03 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:11 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:15 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:18 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:22 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:30 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:30 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:34 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:41 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:47 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:56 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:57 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 23:33:58 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
"""
expected_log2=""
expected_log3="""Feb 14 07:07:39 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
"""
expected_log4="""Feb 14 07:07:01 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 14 07:07:03 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 14 07:07:08 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 14 07:07:15 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 14 07:07:22 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 14 07:07:22 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 14 07:07:25 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 14 07:07:27 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 14 07:07:30 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 14 07:07:38 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 14 07:07:39 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
"""
expected_log5="""Feb 13 18:31:30 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
"""
expected_log6="""Feb 13 18:31:30 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 18:31:36 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 18:31:45 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 18:31:49 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 18:31:57 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 18:31:57 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
Feb 13 18:32:00 web03 haproxy[1631]: 10.350.42.161:58625 [10/Feb/2011:10:59:49.089] frontend pool3/srv28-5020 0/138/0/19/160 200 488 - - ---- 332/332/13/0/0 0/15 {Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7|www.reddit.com|http://www.reddit.com/r/pics/?count=75&after=t3_fiic6|201.8.487.192|17.86.820.117|} "POST /api/vote HTTP/1.1"
"""




#----------------------------------------------------------------------------------------------------------------------
#                                                    The Main Event
#----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  pass
