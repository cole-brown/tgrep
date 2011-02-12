#!/usr/bin/env python2.6
#

from datetime import datetime

if __name__ == '__main__':
  d = datetime.strptime("Feb  9 14:34:43" + str(datetime.now().year), "%b %d %H:%M:%S%Y")
  print d.tzname()
  print d.isoformat()

