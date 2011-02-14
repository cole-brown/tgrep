#!/usr/bin/env python2.6
#

"""Runs all unit tests."""

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
from tests.tgrep_test import TgrepTestCase

#----------------------------------------------------------------------------------------------------------------------
#                                                    The Main Event
#----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(TgrepTestCase)
# suite1 = module1.TheTestSuite()
# suite2 = module2.TheTestSuite()
# alltests = unittest.TestSuite([suite1, suite2])
  unittest.TextTestRunner(verbosity=2).run(suite)
