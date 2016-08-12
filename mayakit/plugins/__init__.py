'''
mayakit.plugins
===============
'''

import os

plugins_path = os.path.join(os.path.dirname(__file__))
try:
    plugin_path = os.environ['MAYA_PLUG_IN_PATH']
    plugin_path = plugins_path + os.pathsep + plugin_path
except KeyError:
    plugin_path = plugins_path
os.environ['MAYA_PLUG_IN_PATH'] = plugin_path


from . import utils
from . import reorderCurve, resampleCurve
