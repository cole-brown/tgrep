# //! stuff? check github for common headers?

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
