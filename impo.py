import imp

def imp_file(config_file):
  try:
    tgrep_config = imp.load_source('tgrep_config', config_file)
    from tgrep_config import stats, config
  except ImportError:
    print "LOADING CONFIG.PY INSTEAD OF WHATEVER YOU ASKED FOR!"
    from config import stats, config


class Foo:
  def __init__(self, config_file):
    try:
      tgrep_config = imp.load_source('tgrep_config', config_file)
      from tgrep_config import stats, config
    except ImportError:
      print "LOADING CONFIG.PY INSTEAD OF WHATEVER YOU ASKED FOR!"
      from config import stats, config
    print config.WIDE_SWEEP_CLOSE_ENOUGH
    self.config = config
    self.stats = stats
  
  def lolwut(self):
    print "CONFIG PRINTING SHUTFUFFF"
    print self.config.WIDE_SWEEP_CLOSE_ENOUGH
    self.stats.edge_sweep_size = 1024



class Bar:
  def __init__(self):
    pass
  
  def lolwut(self):
    print "CONFIG PRINTING SHUTFUFFF"
    print config.WIDE_SWEEP_CLOSE_ENOUGH
    stats.edge_sweep_size = 1024
