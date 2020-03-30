__title__ = 'KRWordRank'
__version__ = '1.0.2'
__author__ = 'Lovit'
__license__ = 'LGPL'
__copyright__ = 'Copyright 2017 Lovit'


import sys
import warnings
if sys.version_info.major < 3:
    warnings.warn('Some functions may not work. We recommend python >= 3.5+')

from . import graph
from . import hangle
from . import sentence
from . import word
