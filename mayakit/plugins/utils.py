from maya import cmds


def is_loaded(plugin):
    '''Is plugin loaded?'''

    return cmds.pluginInfo(plugin, q=True, loaded=True)


def load_plugin(plugin):
    '''Load plugin'''

    if is_loaded(plugin):
        return

    cmds.loadPlugin(plugin)


def unload_plugin(plugin):
    '''Unload plugin'''

    if not is_loaded(plugin):
        return

    cmds.unloadPlugin(plugin, force=False)


def reload_plugin(plugin):
    '''Reload plugin'''

    unload(plugin)
    load(plugin)
