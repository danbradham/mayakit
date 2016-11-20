'''
mayakit.plugins
===============
'''

import os
import imp
import sys
from maya import cmds

plugins_path = os.path.join(os.path.dirname(__file__), 'plugins')

try:
    plugin_path = os.environ['MAYA_PLUG_IN_PATH']
    plugin_path = plugins_path + os.pathsep + plugin_path
except KeyError:
    plugin_path = plugins_path
os.environ['MAYA_PLUG_IN_PATH'] = plugin_path

py_files = [f for f in os.listdir(plugins_path) if f.endswith('.py')]
names = [f.split('.')[0] for f in py_files]


def _import_plugins():
    '''Import plugins from the plugins folder'''

    for f, name in zip(py_files, names):

        full_path = os.path.join(plugins_path, f)
        full_name = 'mayakit.plugins.' + name
        module = imp.load_source(full_name, full_path)
        setattr(sys.modules[__name__], name, module)

_import_plugins()


def is_loaded(plugin):
    '''Is plugin loaded?'''

    return cmds.pluginInfo(plugin, q=True, loaded=True)


def safe_load(plugin):
    '''Load plugin'''

    if is_loaded(plugin):
        return

    cmds.loadPlugin(plugin)


def safe_unload(plugin):
    '''Unload plugin'''

    if not is_loaded(plugin):
        return

    cmds.unloadPlugin(plugin, force=False)


def safe_reload(plugin):
    '''Reload plugin'''

    safe_unload(plugin)
    safe_load(plugin)


def load_all():
    '''Load all mayakit plugins'''

    for name in names:
        safe_load(name)


def unload_all():
    '''Unload all mayakit plugins'''

    for name in names:
        safe_unload(name)


def reload_all():
    '''Reload all mayakit plugins'''

    for name in names:
        safe_reload(name)
