from acolite.shared import *
from acolite import ac
from acolite import acolite
from acolite import aerlut

from acolite import landsat
from acolite import sentinel
from acolite import dem

from acolite import output
from acolite import plotting

##
import os
path = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists('{}{}config'.format(path, os.path.sep)):
    path = os.path.split(path)[0]

    ## check if binary distribution
    if '{}dist{}acolite'.format(os.path.sep,os.path.sep) in path:
        ## two levels for this file
        for i in range(2): path = os.path.split(path)[0]

cfile='{}{}config{}config.txt'.format(path,os.path.sep,os.path.sep)
config = import_config(cfile)

## test whether we can find the relative paths
for t in config:
    if os.path.exists(config[t]): continue
    tmp = path + os.path.sep + config[t]
    config[t] = os.path.abspath(tmp)

