
# Build config and stats objects based on keyword args passed into constructor.

class Configuration:
  def __init__(self, **kw):
    self.__dict__.update(kw)

class Statistics:
  def __init__(self, **kw ):
    self.__dict__.update(kw)
