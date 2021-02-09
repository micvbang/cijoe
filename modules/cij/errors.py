class CIJError(Exception):
    """ Wrapper for all CIJOE errors """


class InitializationError(CIJError):
    """ Raised when failing to initialize data structures """


class InvalidRangeError(Exception):
    """ Raised for range formatting errors """
