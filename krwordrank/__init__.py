import sys
import warnings
if sys.version_info.major < 3:
    warnings.warn('Some functions may not work. We recommend python >= 3.5+')

from . import graph
from . import hangle
from . import sentence
from . import word
