
# Exceptions used in PertGyp

#======================================================================================================================
#                                                   InvalidArgument
#======================================================================================================================
class InvalidArgument(Exception):
  """Exception raised for when a func was passed something it didn't like.

  Attributes:
    msg - explanation of the error.
    arg - the arg (must be stringable via str(arg))
  """

  def __init__(self, msg, arg):
    self.msg = msg
    self.arg = arg

  def __str__(self):
    return "%s\narg: %s\n" % (self.msg, str(self.arg))


#======================================================================================================================
#                                                       NotFound
#======================================================================================================================
class NotFound(Exception):
  """Exception raised for when nothing is found in the log.

  Attributes:
    msg     - explanation of the error.
    times   - min/max array of times looking for
    guesses - nearest guesses when time was discovered not to exist in log
  """

  def __init__(self, msg, times, guesses):
    self.msg = msg
    self.times = times
    self.guesses = guesses

  def __str__(self):
    return "%s\ntimes: %s\nguesses: %s" % (self.msg, self.times, self.guesses)


#======================================================================================================================
#                                                       NotTime
#======================================================================================================================
class NotTime(Exception):
  """Exception raised when a string sent to arg_time_parse is not a time or time range.

  Attributes:
    msg     - explanation of the error.
    input   - string passed in
  """

  def __init__(self, msg, input):
    self.msg = msg
    self.input = input

  def __str__(self):
    return "%s\ninput string: %s" % (self.msg, self.input)


#======================================================================================================================
#                                                      RegexError
#======================================================================================================================
class RegexError(Exception):
  """Exception raised when something's wrong with a regex.

  Attributes:
    msg     - explanation of the error
    regex   - regex string
    input   - string regex was working on
  """

  def __init__(self, msg, regex, input):
    self.msg = msg
    self.regex = regex
    self.input = input

  def __str__(self):
    return "%s\ninput string: %s\nregex string: %s" % (self.msg, self.input, self.regex)

